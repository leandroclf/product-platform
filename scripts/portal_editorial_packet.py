"""Read-only editorial action packet for products absent from LF corporate portal.

No API mutation, secrets, remote URLs, publishing or pull request creation.
Only renders verified registry metadata and clearly marked review placeholders.
"""
from propose_portal_intake import plan

MAX_MISSING = 20


def editorial_packet(registry, catalog):
    candidates = plan(registry, catalog)
    if not candidates:
        return {"status": "NO_INTAKE_REQUIRED", "count": 0, "items": []}
    if len(candidates) > MAX_MISSING:
        return {"status": "BLOCKED_TOO_MANY", "count": len(candidates), "items": []}
    return {
        "status": "EDITORIAL_REVIEW_REQUIRED",
        "count": len(candidates),
        "items": candidates,
    }


def render_packet(packet):
    status = packet.get("status")
    if status == "NO_INTAKE_REQUIRED":
        return "Nenhum produto novo aguardando proposta editorial na comparação atual."
    if status == "BLOCKED_TOO_MANY":
        return "Revisão manual obrigatória: quantidade anormal de produtos sem página."
    if status != "EDITORIAL_REVIEW_REQUIRED":
        return "UNVERIFIED — não foi possível gerar uma proposta editorial confiável."
    lines = [
        "Produtos abaixo foram registrados na plataforma, mas não constam no catálogo remoto.",
        "**Não estão publicados automaticamente e não foram declarados comercialmente disponíveis.**",
        "Produzir PR revisado em site-lf-solucoes antes de expor estas informações publicamente.",
    ]
    for item in packet["items"]:
        name = item["id"]
        if not isinstance(name, str) or not name.replace("-", "").isalnum():
            return "BLOCKED — identidade inválida no relatório editorial."
        lines.extend([
            "",
            "### " + name,
            "- Repositório de origem: " + item["source_repository"],
            "- Domínio registrado: " + item["domain"],
            "- Runtime: " + item["runtime"] + "; onda: " + str(item["wave"]),
            "- Título, descrição, categoria e benefícios: **aguardando validação editorial**.",
            "- URL pública e disponibilidade comercial: **não verificadas**.",
            "- Ação: preparar PR de catálogo + página individual + snapshot do registry.",
        ])
    return "\n".join(lines)
