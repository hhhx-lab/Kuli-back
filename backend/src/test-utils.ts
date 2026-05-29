import type { Express } from "express";
import type Database from "better-sqlite3";
import { createApp } from "./app.js";
import { createMemoryDatabase } from "./database.js";

export type TestContext = {
  app: Express;
  db: Database.Database;
};

export function createTestApp(): TestContext {
  const db = createMemoryDatabase();
  const app = createApp({ db, jwtSecret: "test-secret" });
  return {
    app,
    db
  };
}
