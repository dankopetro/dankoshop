import { NextRequest, NextResponse } from "next/server"

const GITHUB_TOKEN = process.env.GITHUB_TOKEN
const GITHUB_REPO = process.env.GITHUB_REPO || "dankopetro/dankoshop"
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || "main"
const CONTENT_DIR = "storefront/src/content"
const ADMIN_PASSWORD = process.env.CONTENT_ADMIN_PASSWORD || ""

export async function POST(req: NextRequest) {
  if (!GITHUB_TOKEN) {
    return NextResponse.json(
      { error: "GITHUB_TOKEN no está configurado en el servidor" },
      { status: 500 },
    )
  }

  const body = await req.json().catch(() => null)
  if (!body || !body.password || !body.file || !body.data) {
    return NextResponse.json({ error: "Datos incompletos" }, { status: 400 })
  }
  if (body.password !== ADMIN_PASSWORD) {
    return NextResponse.json({ error: "Contraseña incorrecta" }, { status: 401 })
  }

  const file = String(body.file)
  if (!/^[a-zA-Z0-9_-]+\.json$/.test(file)) {
    return NextResponse.json({ error: "Archivo inválido" }, { status: 400 })
  }

  const path = `${CONTENT_DIR}/${file}`
  const content = JSON.stringify(body.data, null, 2) + "\n"

  try {
    // Obtener el SHA actual del archivo
    const shaRes = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/contents/${encodeURIComponent(path)}?ref=${GITHUB_BRANCH}`,
      { headers: { Authorization: `Bearer ${GITHUB_TOKEN}` } },
    )
    const shaBody = await shaRes.json().catch(() => ({}))
    const sha = shaBody.sha

    const commitRes = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/contents/${encodeURIComponent(path)}`,
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${GITHUB_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: `Actualizar contenido: ${file}`,
          content: Buffer.from(content).toString("base64"),
          sha,
          branch: GITHUB_BRANCH,
        }),
      },
    )

    if (!commitRes.ok) {
      const err = await commitRes.text()
      return NextResponse.json({ error: `Error al guardar: ${err}` }, { status: 500 })
    }

    return NextResponse.json({ ok: true })
  } catch (e) {
    return NextResponse.json(
      { error: `Error: ${e instanceof Error ? e.message : String(e)}` },
      { status: 500 },
    )
  }
}
