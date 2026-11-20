"""Export lockfile-backed npm and Python license inventories as CSV."""

import csv
import importlib.metadata
import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "docs" / "ms3" / "legal"
FIELDS = ["Nome", "Versão resolvida", "Tipo", "Utilização", "Licença", "Fonte", "Observações"]

FRONTEND_USAGE = {
    "react": "Biblioteca de interface React",
    "react-dom": "Renderização React no browser",
    "@types/node": "Tipos Node.js para a configuração Vite",
    "@types/react": "Tipos TypeScript para React",
    "@types/react-dom": "Tipos TypeScript para React DOM",
    "@vitejs/plugin-react": "Integração React e Fast Refresh no Vite",
    "oxlint": "Linter JavaScript/TypeScript",
    "typescript": "Verificação de tipos TypeScript",
    "vite": "Servidor de desenvolvimento e build",
}
BACKEND_RUNTIME = {"alembic", "asyncpg", "fastapi", "minio", "pydantic-settings", "sqlalchemy", "uvicorn"}
BACKEND_TEST = {"aiosqlite", "httpx", "pytest", "pytest-asyncio"}
BACKEND_BUILD_TRANSITIVE = {"packaging", "pathspec", "pluggy", "tomlkit", "trove-classifiers"}


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def package_name_from_lock_path(path: str) -> str:
    name = path.rsplit("node_modules/", 1)[-1]
    if name.startswith("@"):
        scope, package = name.split("/", 1)
        return f"{scope}/{package}"
    return name


def frontend_rows() -> list[dict[str, str]]:
    package_file = ROOT / "frontend" / "package.json"
    lock_file = ROOT / "frontend" / "package-lock.json"
    manifest = json.loads(package_file.read_text(encoding="utf-8"))
    lock = json.loads(lock_file.read_text(encoding="utf-8"))
    runtime = set(manifest.get("dependencies", {}))
    development = set(manifest.get("devDependencies", {}))
    rows = [
        {
            "Nome": manifest["name"],
            "Versão resolvida": manifest["version"],
            "Tipo": "Projeto ApontaUA",
            "Utilização": "Código fonte da aplicação; não é uma dependência de terceiros",
            "Licença": manifest.get("license", "Não declarada"),
            "Fonte": "frontend/package.json",
            "Observações": "A licença do código próprio ainda não foi escolhida",
        }
    ]
    packages = lock["packages"]
    for lock_path, item in sorted(packages.items()):
        if not lock_path or "version" not in item:
            continue
        name = package_name_from_lock_path(lock_path)
        if name in runtime:
            kind = "Direta runtime"
            usage = FRONTEND_USAGE.get(name, "Dependência runtime declarada")
        elif name in development:
            kind = "Direta desenvolvimento"
            usage = FRONTEND_USAGE.get(name, "Ferramenta de desenvolvimento declarada")
        else:
            kind = "Transitiva desenvolvimento" if item.get("dev") else "Transitiva runtime"
            usage = "Dependência transitiva"
        notes = []
        if item.get("optional"):
            notes.append("Opcional/condicional, incluindo binding específico de plataforma")
        if name == "typescript":
            notes.append("A distribuição inclui NOTICE.txt; preservar avisos aplicáveis em redistribuição")
        if name in {"lightningcss", "lightningcss-linux-arm64-gnu", "lightningcss-linux-arm64-musl", "lightningcss-linux-x64-gnu", "lightningcss-linux-x64-musl", "lightningcss-darwin-arm64", "lightningcss-darwin-x64", "lightningcss-win32-arm64-msvc", "lightningcss-win32-x64-msvc", "lightningcss-android-arm64", "lightningcss-freebsd-x64", "lightningcss-linux-arm-gnueabihf"} and item.get("license") == "MPL-2.0":
            notes.append("MPL-2.0: rever obrigações por ficheiro se houver modificação/redistribuição")
        rows.append(
            {
                "Nome": name,
                "Versão resolvida": item["version"],
                "Tipo": kind,
                "Utilização": usage,
                "Licença": item.get("license", "Não declarada no lockfile"),
                "Fonte": "frontend/package-lock.json (metadados npm), package.json para dependências diretas",
                "Observações": "; ".join(notes) or "",
            }
        )
    return rows


def distribution_license(dist: importlib.metadata.Distribution) -> tuple[str, str]:
    metadata = dist.metadata
    expression = metadata.get("License-Expression") or metadata.get("License")
    if expression:
        return expression, "Metadados da distribuição (License-Expression/License)"

    classifiers = metadata.get_all("Classifier") or []
    license_classifiers = [c.split(" :: ", 1)[-1] for c in classifiers if c.startswith("License :: ")]
    license_files = []
    for file in dist.files or []:
        name = str(file).lower()
        if "license" in name and not name.endswith((".py", ".pyc")):
            try:
                content = dist.locate_file(file).read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue
            license_files.append((str(file), content[:10000]))

    joined = "\n".join(text for _, text in license_files)
    if "Mozilla Public License Version 2.0" in joined:
        return "MPL-2.0", "Ficheiro LICENSE da distribuição; classifier confirma MPL 2.0"
    if "Apache License" in joined and "Version 2.0" in joined:
        return "Apache-2.0", "Ficheiro LICENSE da distribuição; classifier confirma Apache Software License"
    if license_classifiers:
        return "; ".join(license_classifiers), "Classificador PyPI; expressão SPDX não fornecida"
    if license_files:
        return f"Licença incluída: {license_files[0][0]} (expressão não identificada)", "Ficheiro LICENSE incluído na distribuição"
    return "Não declarada", "Metadados e ficheiros de licença da distribuição sem identificação automática"


def lock_closure(lock: dict, roots: set[str]) -> set[str]:
    """Pacotes alcançáveis a partir de `roots` no grafo de dependências do uv.lock."""
    graph = {
        canonical_name(package["name"]): {
            canonical_name(dependency["name"]) for dependency in package.get("dependencies", [])
        }
        for package in lock["package"]
    }
    seen: set[str] = set()
    pending = [canonical_name(root) for root in roots]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(graph.get(name, set()))
    return seen


def backend_rows() -> list[dict[str, str]]:
    lock_file = ROOT / "uv.lock"
    lock = tomllib.loads(lock_file.read_text(encoding="utf-8"))
    runtime_closure = lock_closure(lock, BACKEND_RUNTIME)
    test_closure = lock_closure(lock, BACKEND_TEST) - runtime_closure
    installed = {
        canonical_name(dist.metadata["Name"]): dist
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    rows = [
        {
            "Nome": "apontaua-backend",
            "Versão resolvida": "0.1.0",
            "Tipo": "Projeto ApontaUA",
            "Utilização": "Código fonte do backend; não é dependência de terceiros",
            "Licença": "Não declarada",
            "Fonte": "pyproject.toml",
            "Observações": "A licença do código próprio ainda não foi escolhida",
        }
    ]
    for item in sorted(lock["package"], key=lambda package: package["name"].lower()):
        name = item["name"]
        if name == "apontaua-backend":
            continue
        normalized = canonical_name(name)
        dist = installed.get(normalized)
        if dist:
            license_name, license_source = distribution_license(dist)
        else:
            license_name, license_source = "Não confirmada", "Pacote não instalado neste ambiente"
        if name in BACKEND_RUNTIME:
            kind = "Direta runtime"
            usage = "Dependência declarada em pyproject.toml"
        elif name == "hatchling":
            kind = "Direta build"
            usage = "Build backend declarado em pyproject.toml e incluído no grupo build"
        elif name in BACKEND_TEST:
            kind = "Direta teste"
            usage = "Ferramenta de testes declarada no grupo test do pyproject.toml"
        elif normalized in test_closure and name not in BACKEND_BUILD_TRANSITIVE:
            kind = "Transitiva teste"
            usage = "Dependência das ferramentas de testes resolvida por uv.lock"
        else:
            kind = "Transitiva build" if name in BACKEND_BUILD_TRANSITIVE else "Transitiva runtime"
            usage = "Dependência resolvida por uv.lock"
        notes = license_source
        if license_name == "MPL-2.0":
            notes += "; rever obrigações por ficheiro em caso de modificação/redistribuição"
        if " OR " in license_name:
            notes += "; expressão alternativa, confirmar a opção de distribuição escolhida"
        rows.append(
            {
                "Nome": name,
                "Versão resolvida": item["version"],
                "Tipo": kind,
                "Utilização": usage,
                "Licença": license_name,
                "Fonte": "uv.lock e metadados/ficheiros LICENSE da distribuição instalada",
                "Observações": notes,
            }
        )
    return rows


if __name__ == "__main__":
    LEGAL.mkdir(parents=True, exist_ok=True)
    write_csv(LEGAL / "frontend-license-inventory.csv", frontend_rows())
    write_csv(LEGAL / "backend-license-inventory.csv", backend_rows())
    print("Inventários frontend/backend exportados a partir dos lockfiles.")
