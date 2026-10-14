/// <reference types="vite/client" />

interface ImportMetaEnv {
  VITE_API_BASE_URL?: string
  [key: string]: unknown
}

interface ImportMeta {
  env: ImportMetaEnv
}
