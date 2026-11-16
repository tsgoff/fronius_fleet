# Integration icon

`fronius_fleet_icon.svg` is the editable vector source for the integration's
original solar fleet icon. It depicts a rising sun and three solar panels in
red (`#E53935`) and navy (`#16324F`). It is not an official Fronius or Home
Assistant logo.

Home Assistant uses the PNG exports in
`custom_components/fronius_fleet/brand/`:

- `icon.png`: 256 × 256 pixels.
- `icon@2x.png`: 512 × 512 pixels.
- `dark_icon.png` / `dark_icon@2x.png`: light blue panels for dark themes.

The images have transparent backgrounds. Since the logo is the same square
symbol, Home Assistant can use the icon as the logo fallback; duplicate
`logo.png` files are not needed.
