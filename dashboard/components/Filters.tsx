"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

const TRADES = [
  "solar panel installer",
  "window installer",
  "kitchen fitter",
  "roofing contractor",
  "house extension builder",
  "loft conversion specialist",
];

const STATUSES = ["new", "reviewed", "contacted", "qualified", "rejected"];

export function Filters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const update = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      params.delete("page");
      router.push(`/?${params.toString()}`);
    },
    [router, searchParams]
  );

  return (
    <div className="flex flex-wrap gap-3">
      <select
        value={searchParams.get("trade") ?? ""}
        onChange={(e) => update("trade", e.target.value)}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All trades</option>
        {TRADES.map((t) => (
          <option key={t} value={t} className="capitalize">
            {t}
          </option>
        ))}
      </select>

      <input
        type="text"
        placeholder="Postcode prefix (e.g. SE1)"
        value={searchParams.get("postcode") ?? ""}
        onChange={(e) => update("postcode", e.target.value)}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">Score ≥</label>
        <input
          type="number"
          min={0}
          max={100}
          step={5}
          value={searchParams.get("minScore") ?? ""}
          onChange={(e) => update("minScore", e.target.value)}
          placeholder="0"
          className="rounded border border-gray-300 px-3 py-1.5 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <select
        value={searchParams.get("status") ?? ""}
        onChange={(e) => update("status", e.target.value)}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All statuses</option>
        {STATUSES.map((s) => (
          <option key={s} value={s} className="capitalize">
            {s}
          </option>
        ))}
      </select>

      {searchParams.toString() && (
        <button
          onClick={() => router.push("/")}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-50"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
