"""Example script: Install an IPA on a device.

Usage:
    iphone-farm run example_install_app --args '{"ipa_path": "/path/to/app.ipa"}'
"""


async def run(ctx, args):
    ipa_path = args.get("ipa_path")
    if not ipa_path:
        raise ValueError("ipa_path is required in args")
    result = await ctx.install_app(ipa_path)
    return result
