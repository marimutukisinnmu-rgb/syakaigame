// Read-only CloudSave export for GitHub Actions.
// Output contains player IDs and save data; the workflow encrypts it before storage.
const endpoint = "https://fra.cloud.appwrite.io/v1";
const projectId = "6ad7592f0030063027da";
const databaseId = "cloudsave";
const tableId = "saves";
const apiKey = process.env.APPWRITE_API_KEY;

if (!apiKey) throw new Error("APPWRITE_API_KEY is required");

const headers = {
  "X-Appwrite-Project": projectId,
  "X-Appwrite-Key": apiKey,
  "Content-Type": "application/json",
};

const rows = [];
const pageSize = 100;
let total = null;

for (let offset = 0; total === null || offset < total; offset += pageSize) {
  const params = new URLSearchParams();
  params.append("queries[]", JSON.stringify({ method: "limit", values: [pageSize] }));
  params.append("queries[]", JSON.stringify({ method: "offset", values: [offset] }));

  const response = await fetch(
    `${endpoint}/tablesdb/${encodeURIComponent(databaseId)}/tables/${encodeURIComponent(tableId)}/rows?${params.toString()}`,
    { method: "GET", headers, signal: AbortSignal.timeout(30_000) }
  );

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 500);
    throw new Error(`Appwrite export failed (HTTP ${response.status}): ${detail}`);
  }

  const page = await response.json();
  if (!Array.isArray(page.rows) || !Number.isInteger(page.total)) {
    throw new Error("Unexpected Appwrite response; refusing to create a partial backup.");
  }
  if (total === null) total = page.total;
  if (page.total !== total) {
    throw new Error("CloudSave row count changed during export; retry the backup.");
  }
  rows.push(...page.rows);
  if (page.rows.length === 0 && rows.length < total) {
    throw new Error("Appwrite returned an empty page before all rows were exported.");
  }
}

const output = {
  schemaVersion: 1,
  source: { projectId, databaseId, tableId },
  createdAt: new Date().toISOString(),
  total: rows.length,
  rows,
};

if (output.total !== total) {
  throw new Error("Export count mismatch; refusing to create an incomplete backup.");
}

process.stdout.write(JSON.stringify(output));
