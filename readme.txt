=== Webchanges – AI Connector (MCP) ===
Contributors: shahbazdev
Tags: mcp, ai, automation, content, seo
Requires at least: 6.9
Tested up to: 7.1
Requires PHP: 8.0
Stable tag: 1.0.0
License: AGPLv3 or later
License URI: https://www.gnu.org/licenses/agpl-3.0.html

Connect WordPress to MCP-compatible AI clients so agents can manage content, media, SEO, forms, and site settings over the Model Context Protocol.

== Description ==

Webchanges – AI Connector (MCP) turns your WordPress site into a Model Context Protocol (MCP) server, so an AI client you control (any MCP-compatible client) can manage the site through a gated, auditable set of "abilities" built on the WordPress Abilities API.

Capabilities include:

* Posts, pages and blocks (Gutenberg, Bricks, Elementor).
* Media — upload, sideload, alt text, and autonomous in-place image optimization (compress, resize, WebP).
* SEO — Rank Math / Yoast meta, redirects, and Yoast Search Appearance settings.
* Forms — Formidable, Fluent Forms, WPForms, Forminator (create/edit, settings, notifications, list submissions).
* Taxonomies, menus, users, WooCommerce, ACF, and site settings.
* A Bricks "design compiler" that turns an HTML/CSS design into a native Bricks page.

Only three meta tools are exposed over MCP (discover-abilities, get-ability-info, execute-ability); every individual ability is gated per install from the Abilities Manager, and the MCP transport requires the `manage_options` capability. This edition ships **no** arbitrary-code-execution or direct filesystem-write abilities.

= Requirements =

* WordPress 6.9+ (the Abilities API is included in core), or the standalone "Abilities API" plugin on older versions.
* PHP 8.0+.
* An MCP-compatible AI client to connect.

== External services ==

This plugin contacts no external service on its own initiative - nothing is sent in the background, on activation, or on a schedule. A third-party service is reached only when an action you run (or that an AI client you have authorised runs) uses it. Every provider below except Pollinations additionally requires you to save that provider's API key before it can be reached:

* **OpenAI** (optional, image generation) — when you add an OpenAI API key and an agent generates/edits an image, the prompt (and, for edits, the source image) is sent to api.openai.com. Terms: https://openai.com/policies/terms-of-use — Privacy: https://openai.com/policies/privacy-policy
* **Google Gemini / Imagen** (optional, image generation) — when configured, prompts are sent to generativelanguage.googleapis.com. Terms: https://ai.google.dev/gemini-api/terms — Privacy: https://policies.google.com/privacy
* **Replicate** (optional, image generation) — when configured, prompts are sent to api.replicate.com. Terms: https://replicate.com/terms — Privacy: https://replicate.com/privacy
* **Pollinations** (optional, image generation - no API key needed) - the only provider that needs no key, so it can be used without configuring anything. It is never a default and never an automatic fallback: it is contacted only when an image-generation request explicitly names the `pollinations` provider, and only your image prompt and the requested dimensions are sent to image.pollinations.ai. Terms: https://pollinations.ai/terms - Privacy: https://pollinations.ai/privacy
* **Pexels / Unsplash / Pixabay** (optional, stock photos) — when you add a key and an agent fetches stock photos, your search query is sent to the respective API. Pexels: https://www.pexels.com/terms-of-service/ , https://www.pexels.com/privacy-policy/ — Unsplash: https://unsplash.com/terms , https://unsplash.com/privacy — Pixabay: https://pixabay.com/service/terms/ , https://pixabay.com/service/privacy/

Optional, opt-in usage telemetry (OFF by default): if — and only if — you turn it on, the plugin sends your site URL, site name, plugin/WordPress/PHP versions, and multisite flag to https://webchanges.searchactions.com/api/plugin/activations so the maintainer can count active installs. No content or credentials are ever sent. Nothing is transmitted unless you opt in.

== Installation ==

1. On WordPress 6.9+ the Abilities API is built in. On older versions, install and activate the "Abilities API" plugin first (https://wordpress.org/plugins/abilities-api/).
2. Upload this plugin and activate it.
3. Open the Webchanges admin page, enable the connector, and create a WordPress Application Password.
4. Add the shown MCP endpoint + credentials to your AI client, and enable the abilities you want from the Abilities Manager.

== Frequently Asked Questions ==

= Does it run arbitrary code or write arbitrary files? =
No. This edition ships no PHP-execution or filesystem write/read abilities.

= Who can use the connection? =
The MCP endpoint requires a `manage_options` (administrator) application password, and high-risk actions are gated per ability.

= Does it phone home? =
No, unless you explicitly opt in to usage telemetry. It is off by default.

== Changelog ==

= 1.0.0 =
* Initial public release: MCP server for WordPress with content, media (incl. autonomous image optimization), SEO, forms, Bricks/Elementor, image generation and stock-photo abilities.

== Upgrade Notice ==

= 1.0.0 =
Initial release.
