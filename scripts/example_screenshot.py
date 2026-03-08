"""Example script: Take a screenshot and save it.

Usage:
    iphone-farm run example_screenshot --args '{"output_dir": "./screenshots"}'
"""

from pathlib import Path
from datetime import datetime


async def run(ctx, args):
    output_dir = Path(args.get("output_dir", "./screenshots"))
    output_dir.mkdir(parents=True, exist_ok=True)

    png_data = await ctx.screenshot()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"{ctx.udid[:8]}_{timestamp}.png"
    filename.write_bytes(png_data)
    return f"Screenshot saved to {filename}"
