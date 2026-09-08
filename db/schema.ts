import { index, integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';

export const onlineSessions = sqliteTable('online_sessions', {
  sessionId: text('session_id').primaryKey(),
  lastSeen: integer('last_seen').notNull(),
}, table => [
  index('idx_online_sessions_last_seen').on(table.lastSeen),
]);

export const pageViews = sqliteTable('page_views', {
  viewId: text('view_id').primaryKey(),
  sessionId: text('session_id').notNull(),
  viewedAt: integer('viewed_at').notNull(),
}, table => [
  index('idx_page_views_viewed_at').on(table.viewedAt),
]);
