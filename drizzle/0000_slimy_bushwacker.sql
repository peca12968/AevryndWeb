CREATE TABLE `online_sessions` (
	`session_id` text PRIMARY KEY NOT NULL,
	`last_seen` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_online_sessions_last_seen` ON `online_sessions` (`last_seen`);--> statement-breakpoint
CREATE TABLE `page_views` (
	`view_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`viewed_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_page_views_viewed_at` ON `page_views` (`viewed_at`);--> statement-breakpoint
PRAGMA optimize;
