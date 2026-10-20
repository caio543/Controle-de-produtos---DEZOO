"""Importação assistida de atas em PDF e pastas públicas do Google Drive.

Nenhuma informação extraída é gravada sem confirmação do operador.
"""

import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import fitz
import pandas as pd


ITEM_PATTERN = re.compile(r"^\s*(\d{1,4})\s+(.+)$")
MONEY_PATTERN = re.compile(r"R\$\s*([\d.]+,\d{2,4})")
QTY_PATTERN = re.compile(r"(\d[\d.,]*)\s*(kg|quilo|quilos|sc|saco|sacos|und|unid(?:ade)?s?|fr|frasco|cx|caixa|kit|l|litro|fardo|pct)\b", re.I)


def decimal_br(value):
    """Interpreta número em notação brasileira sem arredondar quantidades."""
    raw = str(value or "").replace("R$", "").replace("\xa0", " ").strip()
    raw = re.sub(r"[^\d,.]", "", raw)
    if not raw:
        return None
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


def metadados(texto, filename):
    """Extrai os identificadores da ata, pregão e empresa do cabeçalho."""
    ata = re.search(r"Ata\s+de\s+Registro\s+de\s+Preços\s*N[º°o.]*\s*(\d{1,5}\s*/\s*\d{4})", texto, re.I)
    pregao = re.search(r"Pregão\s*(?:Eletrônico\s*)?N[º°o.]*\s*(\d{1,6}\s*/\s*\d{4})", texto, re.I)
    processo = re.search(r"(?:Processo\s*(?:administrativo)?\s*n[º°o.]*\s*)(\d{5}\.\d{6}/\d{4}-\d{2})",texto,re.I)
    empresa = re.search(r"(?:Empresa\s+)([^\n,]+?)(?:,\s*CNPJ|\s+CNPJ)", texto,re.I)
    cnpj = re.search(r"CNPJ\s*(?:/MF)?\s*(?:sob\s+o\s+n[º°o.]*\s*)?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})",texto,re.I)
    contato_texto = texto[empresa.end():empresa.end()+1200] if empresa else texto[:2000]
    emails=re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",contato_texto)
    telefone=re.search(r"(?:telefone|fone)\s*:?[\s]*(\(?\d{2}\)?\s*\d{4,5}[ -]?\d{4})",contato_texto,re.I)
    fallback = re.search(r"Ata[_\s-]*(\d{1,5})",filename,re.I)
    return {
        "ata": ata.group(1).replace(" ","") if ata else (f"{fallback.group(1)}/????" if fallback else ""),
        "pregao": pregao.group(1).replace(" ","") if pregao else "",
        "processo": processo.group(1) if processo else "",
        "fornecedor": empresa.group(1).strip() if empresa else "",
        "cnpj_fornecedor": cnpj.group(1) if cnpj else "",
        "email": emails[0] if emails else "",
        "telefone": telefone.group(1) if telefone else "",
    }


def _normalize_cell(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _parse_table_row(row):
    """Lê colunas de uma tabela, sem criar itens a partir de campos duvidosos."""
    cells=[_normalize_cell(x) for x in row]
    if len(cells)<5 or not re.fullmatch(r"\d{1,4}",cells[0]):
        return None
    item=cells[0]
    description=cells[1]
    if len(description)<5: return None
    # Atas do pregão 35/2026: ITEM | ESPECIFICAÇÃO | QUANT. | UNIDADE | MARCA | VALOR UNITÁRIO
    if len(cells)>=6:
        qtd=decimal_br(cells[2]); unidade=cells[3]; marca=cells[4]; preco=decimal_br(cells[5])
    else:
        qtd=None;unidade="";marca="";preco=None
        joined=" ".join(cells[2:]); qm=QTY_PATTERN.search(joined); pm=MONEY_PATTERN.search(joined)
        if qm: qtd=decimal_br(qm.group(1));unidade=qm.group(2)
        if pm: preco=decimal_br(pm.group(1))
    if qtd is None or preco is None or not unidade: return None
    return {"item":item,"produto":description,"quantidade":qtd,"unidade":unidade,"marca":marca,"preco":preco,"origem":"Tabela PDF"}


def extrair_pdf(pdf_bytes, filename):
    """Retorna metadados, itens com extração verificável e mensagens de atenção."""
    doc=fitz.open(stream=pdf_bytes,filetype="pdf")
    texto="\n".join(page.get_text(sort=True) for page in doc)
    meta=metadados(texto,filename)
    linhas=[]
    for page in doc:
        try:
            finder=page.find_tables()
            for table in finder.tables:
                for row in table.extract():
                    candidate=_parse_table_row(row)
                    if candidate: linhas.append(candidate)
        except Exception:
            pass
    # Complemento para PDFs nos quais as tabelas não são detectadas como tabelas nativas.
    # Só aceita linha com número, quantidade/unidade e preço, para evitar extrair cláusulas.
    if not linhas:
        bloco=re.split(r"2\.2\.\s*A\s+listagem",texto,flags=re.I)[0]
        bloco=re.split(r"2\.\s*DOS\s+PREÇOS",bloco,flags=re.I)[-1]
        chunks=re.split(r"(?m)^\s*(\d{1,3})\s+(?=[A-ZÁÉÍÓÚÃÕÇ]|[A-Z][a-z])",bloco)
        for i in range(1,len(chunks)-1,2):
            item=chunks[i]; content=re.sub(r"\s+"," ",chunks[i+1]).strip()
            price=MONEY_PATTERN.search(content)
            qty=QTY_PATTERN.search(content)
            if not price or not qty or not (5<=len(content)<=2500): continue
            description=content[:qty.start()].strip()
            if len(description)<8: continue
            linhas.append({"item":item,"produto":description,"quantidade":decimal_br(qty.group(1)),"unidade":qty.group(2),"marca":"","preco":decimal_br(price.group(1)),"origem":"Texto PDF (revisar)"})
    unique={}
    for row in linhas:
        unique[row["item"]]=row
    avisos=[]
    if not meta["ata"]: avisos.append("Número da ata não identificado no PDF.")
    if not meta["pregao"]: avisos.append("Pregão não identificado; preencha na conferência.")
    if not meta["fornecedor"]: avisos.append("Fornecedor não identificado; preencha na conferência.")
    if not unique: avisos.append("Não foi possível identificar itens com quantidade e preço confiáveis. Confira o PDF e use cadastro manual ou outra versão do arquivo.")
    return meta,list(unique.values()),avisos


def baixar_drive_publico(url):
    """Obtém PDFs de arquivo ou pasta pública pelo gdown, sem credenciais."""
    import gdown
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in {"drive.google.com","docs.google.com"}:
        raise ValueError("Informe um link HTTPS público do Google Drive.")
    with tempfile.TemporaryDirectory() as folder:
        if "/folders/" in parsed.path:
            paths=gdown.download_folder(url=url,output=folder,quiet=True,use_cookies=False,remaining_ok=True)
            if not paths: raise ValueError("Não foi possível listar os arquivos da pasta pública. Confira o compartilhamento ou anexe os PDFs diretamente.")
            pdf_paths=[Path(p) for p in paths if p and str(p).lower().endswith(".pdf")]
        else:
            target=str(Path(folder)/"documento.pdf")
            file_id=re.search(r"/d/([\w-]+)",parsed.path)
            if file_id: result=gdown.download(id=file_id.group(1),output=target,quiet=True,use_cookies=False)
            else: result=gdown.download(url=url,output=target,quiet=True,use_cookies=False,fuzzy=True)
            pdf_paths=[Path(result)] if result and str(result).lower().endswith(".pdf") else []
        if not pdf_paths: raise ValueError("O link não retornou PDFs acessíveis. Use o upload manual.")
        if len(pdf_paths)>100: raise ValueError("Limite de 100 PDFs por importação.")
        output=[]
        for path in pdf_paths:
            if path.exists() and path.stat().st_size<=20_000_000:
                output.append((path.name,path.read_bytes()))
        return output


def criar_previa(arquivos):
    """Monta tabela de conferência; erros por arquivo não interrompem os demais."""
    rows=[];warnings=[]
    for filename,content in arquivos:
        try:
            meta,items,alerts=extrair_pdf(content,filename)
            warnings.extend(f"{filename}: {a}" for a in alerts)
            for item in items:
                rows.append({"Selecionar":False,"Pregão":meta["pregao"],"Ata":meta["ata"],"Fornecedor":meta["fornecedor"],"CNPJ":meta["cnpj_fornecedor"],"E-mail":meta["email"],"Telefone":meta["telefone"],"Item":item["item"],"Produto / especificação":item["produto"],"Quantidade":item["quantidade"],"Unidade":item["unidade"],"Marca":item["marca"],"Preço unitário":item["preco"],"Documento":filename,"Origem da extração":item["origem"]})
        except Exception as exc:
            warnings.append(f"{filename}: erro de leitura ({str(exc)[:180]}).")
    df=pd.DataFrame(rows)
    return df,warnings
