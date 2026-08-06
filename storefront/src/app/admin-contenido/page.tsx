import { contentPages } from "@/content"
import EditorClient from "./editor-client"

export const metadata = { title: "Editor de Contenido" }

export default function AdminContenidoPage() {
  return <EditorClient pages={contentPages} />
}
