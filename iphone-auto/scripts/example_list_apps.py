"""Example script: List all user apps on a device.

Scripts must define an async `run(ctx, args)` function.
`ctx` is a DeviceContext providing device operations.
`args` is a dict of user-provided arguments.
"""


async def run(ctx, args):
    apps = await ctx.list_apps()
    app_names = []
    for bundle_id, info in apps.items():
        name = info.get("CFBundleDisplayName", info.get("CFBundleName", bundle_id))
        app_names.append(f"{name} ({bundle_id})")
    return f"Found {len(app_names)} apps:\n" + "\n".join(app_names)
