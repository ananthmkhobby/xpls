from __future__ import annotations

import argparse
from pathlib import Path

from app.config import load_config
from app.crawler import WebsiteCrawler
from app.excel_io import (
    detect_header_row,
    ensure_columns,
    format_output,
    is_processed,
    iter_records,
    load_workbook_for_enrichment,
    write_result,
)
from app.logger import append_error, setup_logging
from app.parser import build_result
from app.sales_automation import apply_sales_automation, create_sales_sheets
from app.validators import normalized_domain

DEFAULT_INPUT = "Xperimentor NGO Master — LIVE .xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich NGO contacts from official websites.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input .xlsx file")
    parser.add_argument("--output", default="outputs/ngo_enriched.xlsx", help="Output .xlsx file")
    parser.add_argument("--config", default="config.yaml", help="YAML config path")
    parser.add_argument("--no-resume", action="store_true", help="Reprocess rows even if they already have results")
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of rows to process")
    parser.add_argument("--sales-automation", action="store_true", help="Add sales scoring, segmentation, and outreach copy")
    parser.add_argument("--skip-crawl", action="store_true", help="Only transform the workbook; do not crawl websites")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    logger = setup_logging()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = load_workbook_for_enrichment(input_path)
    ws = wb.active
    header_row = detect_header_row(ws)
    headers = ensure_columns(ws, header_row)
    crawler = WebsiteCrawler(config, logger)
    cache = {}
    processed = 0

    if not args.skip_crawl:
        for row, ngo_name, website in iter_records(ws, header_row, headers):
            if args.limit and processed >= args.limit:
                break
            if is_processed(ws, row, headers, resume=not args.no_resume):
                logger.info("Skipping already processed row %s: %s", row, ngo_name)
                continue
            logger.info("Processing row %s: %s", row, ngo_name)
            try:
                domain = normalized_domain(website)
                if domain in cache:
                    result = cache[domain]
                else:
                    crawl_result = crawler.crawl(website)
                    result = build_result(crawl_result.pages, config, crawl_result.errors, ngo_name, website)
                    cache[domain] = result
                write_result(ws, row, headers, result)
                for error in result.errors:
                    append_error(row, ngo_name, website, error, "See run.log")
            except Exception as exc:
                logger.exception("Failed row %s: %s", row, ngo_name)
                append_error(row, ngo_name, website, "PARSING_ERROR", str(exc))
            processed += 1
            if processed % config.checkpoint_every == 0:
                if args.sales_automation:
                    headers = ensure_columns(ws, header_row)
                    apply_sales_automation(ws, header_row, headers)
                format_output(ws, header_row, headers)
                wb.save(output_path)
                logger.info("Checkpoint saved to %s", output_path)

    if args.sales_automation:
        headers = ensure_columns(ws, header_row)
        apply_sales_automation(ws, header_row, headers)
        create_sales_sheets(wb, ws, header_row, headers)

    format_output(ws, header_row, headers)
    wb.save(output_path)
    logger.info("Finished. Output saved to %s", output_path)


if __name__ == "__main__":
    main()
