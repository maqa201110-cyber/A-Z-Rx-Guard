import { relations } from "drizzle-orm";
import {
  integer,
  pgTable,
  serial,
  text,
  timestamp,
} from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const shopUsersTable = pgTable("shop_users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const shopSessionsTable = pgTable("shop_sessions", {
  tokenHash: text("token_hash").primaryKey(),
  userId: integer("user_id")
    .notNull()
    .references(() => shopUsersTable.id, { onDelete: "cascade" }),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const shopListingsTable = pgTable("shop_listings", {
  id: serial("id").primaryKey(),
  userId: integer("user_id")
    .notNull()
    .references(() => shopUsersTable.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  model: text("model").notNull(),
  hp: text("hp"),
  type: text("type").notNull(),
  price: text("price").notNull(),
  cpmId: text("cpm_id").notNull(),
  contact: text("contact").notNull(),
  tags: text("tags").array().notNull().default([]),
  description: text("description"),
  images: text("images").array().notNull().default([]),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const shopUsersRelations = relations(shopUsersTable, ({ many }) => ({
  sessions: many(shopSessionsTable),
  listings: many(shopListingsTable),
}));

export const shopSessionsRelations = relations(
  shopSessionsTable,
  ({ one }) => ({
    user: one(shopUsersTable, {
      fields: [shopSessionsTable.userId],
      references: [shopUsersTable.id],
    }),
  }),
);

export const shopListingsRelations = relations(
  shopListingsTable,
  ({ one }) => ({
    seller: one(shopUsersTable, {
      fields: [shopListingsTable.userId],
      references: [shopUsersTable.id],
    }),
  }),
);

export const insertShopUserSchema = createInsertSchema(shopUsersTable).omit({
  id: true,
  createdAt: true,
});
export const insertShopSessionSchema = createInsertSchema(
  shopSessionsTable,
).omit({ createdAt: true });
export const insertShopListingSchema = createInsertSchema(
  shopListingsTable,
).omit({ id: true, createdAt: true });

export type InsertShopUser = z.infer<typeof insertShopUserSchema>;
export type InsertShopSession = z.infer<typeof insertShopSessionSchema>;
export type InsertShopListing = z.infer<typeof insertShopListingSchema>;
export type ShopUser = typeof shopUsersTable.$inferSelect;
export type ShopListing = typeof shopListingsTable.$inferSelect;