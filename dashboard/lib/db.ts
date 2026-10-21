import Database from "better-sqlite3";
import path from "path";

const DB_PATH =
  process.env.DB_PATH ||
  path.join(process.cwd(), "..", "data", "leads.db");

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true, fileMustExist: false });
    _db.pragma("journal_mode = WAL");
  }
  return _db;
}
