#!/usr/bin/env python3
"""
Demo script for L'œil Research Memo Generator

Usage:
    python demo.py cursor.sh
    python demo.py cursor.sh --company "Cursor"
    python demo.py cursor.sh --trigger "headcount_growth" --trigger-value "85% QoQ"
    python demo.py cursor.sh --output memos/cursor.md
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import generate_memo
from src.output.markdown import save_memo


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an investment research memo for a company",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python demo.py cursor.sh
    python demo.py nightfall.ai --company "Nightfall AI"
    python demo.py cursor.sh --trigger headcount_growth --trigger-value "85% QoQ"
    python demo.py cursor.sh -o memos/cursor.md -v
        """
    )
    
    parser.add_argument(
        "domain",
        help="Company domain (e.g., cursor.sh, nightfall.ai)"
    )
    
    parser.add_argument(
        "--company", "-c",
        help="Company name (defaults to domain name)"
    )
    
    parser.add_argument(
        "--trigger", "-t",
        default="Manual review",
        help="Trigger signal type (e.g., headcount_growth)"
    )
    
    parser.add_argument(
        "--trigger-value", "-tv",
        help="Trigger signal value (e.g., '85%% QoQ')"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (defaults to stdout)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger("demo")
    
    # Derive company name from domain if not provided
    company = args.company or args.domain.split(".")[0].title()
    
    # Build trigger info
    trigger = {
        "signal": args.trigger,
        "date": None,
    }
    if args.trigger_value:
        trigger["value"] = args.trigger_value
    
    logger.info(f"Generating research memo for {company} ({args.domain})")
    logger.info(f"Trigger: {trigger['signal']}" + (f" = {trigger.get('value')}" if trigger.get('value') else ""))
    
    # Check for required API keys
    missing_keys = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing_keys.append("ANTHROPIC_API_KEY")
    
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
        logger.warning("Some features may not work. Set environment variables to enable.")
    
    # Generate memo
    try:
        result = await generate_memo(
            company=company,
            domain=args.domain,
            trigger=trigger,
        )
        
        memo = result.get("memo", "[No memo generated]")
        errors = result.get("errors", [])
        sources = result.get("sources_used", [])
        confidence = result.get("confidence", "unknown")
        
        # Report results
        logger.info(f"Sources used: {', '.join(sources) if sources else 'none'}")
        logger.info(f"Confidence: {confidence}")
        
        if errors:
            logger.warning(f"Errors encountered: {len(errors)}")
            for err in errors:
                logger.warning(f"  - {err}")
        
        # Output memo
        if args.output:
            # Ensure directory exists
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            save_memo(memo, str(output_path))
            logger.info(f"Memo saved to {args.output}")
        else:
            print("\n" + "=" * 80)
            print(memo)
            print("=" * 80 + "\n")
        
        # Return success/failure based on confidence
        return 0 if confidence != "low" else 1
        
    except Exception as e:
        logger.error(f"Memo generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
