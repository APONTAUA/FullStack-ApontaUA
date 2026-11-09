# Frontend ApontaUA

Aplicação React + TypeScript + Vite. Este scaffold contém apenas a estrutura e
uma página inicial mínima; autenticação, rotas, estado e funcionalidades ainda
não foram implementados.

## Estrutura

```text
src/
  app/                 composição da aplicação e providers
  features/            módulos funcionais descritos em features/README.md
  services/api/        configuração e cliente HTTP
  shared/              código reutilizado entre módulos
  styles/              estilos globais e tokens visuais
  assets/              imagens e outros recursos importados pelo código
main.tsx               ponto de entrada React
```

`public/` contém recursos servidos sem processamento pelo Vite. O frontend é
independente do microsite Docusaurus existente no repositório de documentação.

## Arranque

```bash
cp .env.example .env
npm ci
npm run dev
```

O `package-lock.json` deve acompanhar o `package.json`; `npm ci` instala as
versões nele fixadas. Requer Node.js 20.19+ ou 22.12+, de acordo com os
requisitos atuais do Vite.
