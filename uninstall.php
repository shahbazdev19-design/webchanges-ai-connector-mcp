<?php

declare(strict_types=1);

/**
 * Uninstall cleanup for Webchanges – AI Connector (MCP).
 *
 * Runs only when the plugin is deleted from the Plugins screen (not on
 * deactivation). Removes every option, transient, scheduled event and file the
 * connector creates — including the encrypted third-party API keys, which must
 * not survive deletion.
 *
 * Deliberately left alone: application passwords (user-owned WordPress
 * credentials, not plugin data) and anything the abilities wrote into other
 * plugins' or core's options (posts, media, `blog_public`, Bricks/Yoast data).
 *
 * @package Webchanges_AI_Connector_MCP
 */

if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit();
}

/**
 * Options with fixed names. Keep in sync with the writers in includes/.
 */
function webchanges_connector_uninstall_options(): array
{
    return [
        'webchanges_connector_enabled',
        'webchanges_connector_enabled_dangerous',
        'webchanges_connector_disabled_abilities',
        'webchanges_connector_disabled_skills',
        'webchanges_connector_domain',
        'webchanges_connector_image_gen',      // OpenAI / Gemini / Replicate keys
        'webchanges_connector_stock',          // stock-photo provider keys
        'webchanges_connector_secret_material', // encryption key material
        'webchanges_connector_skills',
        'webchanges_connector_jobs_latest',
        'webchanges_connector_version',
        'webchanges_connector_delivery_fallback',
    ];
}

/**
 * Wipe every trace of the connector from the current site.
 */
function webchanges_connector_uninstall_site(): void
{
    global $wpdb;

    foreach (webchanges_connector_uninstall_options() as $option) {
        delete_option($option);
    }

    // Per-job options (`webchanges_connector_job_<id>`) and job lock transients
    // (`wcc_job_lock_<id>`) are created dynamically, so they need a LIKE sweep.
    $patterns = [
        $wpdb->esc_like('webchanges_connector_job_') . '%',
        $wpdb->esc_like('_transient_wcc_job_lock_') . '%',
        $wpdb->esc_like('_transient_timeout_wcc_job_lock_') . '%',
    ];
    foreach ($patterns as $like) {
        // phpcs:ignore WordPress.DB.DirectDatabaseQuery.DirectQuery,WordPress.DB.DirectDatabaseQuery.NoCaching -- one-time uninstall sweep of dynamically-named options; no caching layer applies.
        $names = $wpdb->get_col($wpdb->prepare("SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE %s", $like));
        foreach ((array) $names as $name) {
            delete_option((string) $name);
        }
    }

    wp_clear_scheduled_hook('webchanges_connector_job_run');
}

/**
 * Remove files the plugin drops outside its own directory.
 *
 * Site-independent, so this runs once rather than per blog.
 */
function webchanges_connector_uninstall_files(): void
{
    require_once ABSPATH . 'wp-admin/includes/file.php';

    global $wp_filesystem;
    if (!WP_Filesystem()) {
        return; // No credentials — leave the files rather than guessing.
    }

    // The WebP delivery drop-in, when mu-plugins/ was writable.
    if (defined('WPMU_PLUGIN_DIR')) {
        $mu = trailingslashit(WPMU_PLUGIN_DIR) . 'webchanges-image-delivery.php';
        if ($wp_filesystem->is_file($mu)) {
            $wp_filesystem->delete($mu);
        }
    }

    // The sandbox working directory — only when nothing was left inside it.
    $sandbox = trailingslashit(WP_CONTENT_DIR) . 'webchanges-sandbox/';
    if ($wp_filesystem->is_dir($sandbox) && !$wp_filesystem->dirlist($sandbox)) {
        $wp_filesystem->rmdir($sandbox);
    }
}

if (is_multisite()) {
    foreach (get_sites(['fields' => 'ids', 'number' => 0]) as $blog_id) {
        switch_to_blog((int) $blog_id);
        webchanges_connector_uninstall_site();
        restore_current_blog();
    }
} else {
    webchanges_connector_uninstall_site();
}

webchanges_connector_uninstall_files();
