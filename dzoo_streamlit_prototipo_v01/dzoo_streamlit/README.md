# DZOO · Gestão de Aquisições (protótipo v0.1)

Protótipo operacional do Departamento de Zootecnia da UFSJ, com navegação por produto e por processo, planejamento, atas, PPLAN, requisições, empenhos, recebimentos, DANFEs, relatórios e geração de rascunhos.

## Instalação local

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Publicação

1. Envie `app.py`, `requirements.txt` e `.gitignore` a um repositório no GitHub.
2. Crie um aplicativo em https://share.streamlit.io e selecione `app.py`.
3. **Atenção:** SQLite é utilizado apenas para testes locais. Na Streamlit Community Cloud, os arquivos locais não são persistência segura; cadastros podem desaparecer após reinicialização. Não utilize dados administrativos reais na implantação pública antes de integrar banco persistente, autenticação e controle de acesso.

## Avisos importantes

- Banco começa vazio. Na barra lateral há opção **Popular dados fictícios** para experimentar. Esses dados são identificados como exemplos e podem ser apagados com **Limpar dados de demonstração**.
- Não existe integração real com SIPAC, Compras.gov.br, PNCP ou e-mail; o aplicativo gera rascunhos e permite registro manual.
- Valores e saldos refletem **somente aquisições registradas no aplicativo**. Não são saldos oficiais do SIPAC.
- Registrar notas fiscais não significa que elas foram atestadas ou pagas.
- No protótipo, cada DANFE pertence a uma entrega; vários DANFEs da mesma entrega podem conter o mesmo produto. As quantidades por DANFE são somadas exatamente uma vez.
- Não há autenticação nesta versão: use somente em ambiente local, com dados de teste.
