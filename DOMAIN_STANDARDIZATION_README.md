# Padronização de Domínios no PepperPy

Este documento explica como usar os scripts de padronização para garantir que todos os domínios do projeto PepperPy sigam as convenções de arquivos definidas.

## Convenções de Arquivos

As convenções de arquivos para os domínios estão definidas no arquivo [DOMAIN_FILE_CONVENTIONS.md](DOMAIN_FILE_CONVENTIONS.md). Cada domínio deve conter os seguintes arquivos obrigatórios:

1. **`__init__.py`**: Exporta as principais classes e funções do domínio, define a API pública.
2. **`base.py`**: Contém classes base e interfaces abstratas que definem o comportamento do domínio.
3. **`types.py`**: Define tipos, enums, e estruturas de dados específicas do domínio.
4. **`factory.py`**: Implementa padrões de fábrica para criar instâncias de classes do domínio.
5. **`registry.py`**: Gerencia o registro de implementações e plugins para o domínio.

## Scripts Disponíveis

### Verificação de Conformidade

Para verificar se um domínio está em conformidade com as convenções de arquivos, use o script `check_domains.sh`:

```bash
# Verificar um domínio específico
./scripts/check_domains.sh --domain nome_do_dominio

# Verificar todos os domínios
./scripts/check_domains.sh --all
```

### Padronização de Domínios

Para padronizar um domínio existente, adicionando os arquivos obrigatórios que estão faltando, use o script `standardize_domain.sh`:

```bash
# Padronizar um domínio específico
./scripts/standardize_domain.sh --domain nome_do_dominio
```

Para padronizar todos os domínios de uma vez, use o script `standardize_all_domains.sh`:

```bash
# Padronizar todos os domínios
./scripts/standardize_all_domains.sh
```

## Fluxo de Trabalho Recomendado

1. Verifique quais domínios não estão em conformidade com as convenções:
   ```bash
   ./scripts/check_domains.sh --all
   ```

2. Padronize os domínios que não estão em conformidade:
   ```bash
   # Padronizar um domínio específico
   ./scripts/standardize_domain.sh --domain nome_do_dominio
   
   # Ou padronizar todos os domínios de uma vez
   ./scripts/standardize_all_domains.sh
   ```

3. Verifique novamente para garantir que todos os domínios estão em conformidade:
   ```bash
   ./scripts/check_domains.sh --all
   ```

## Padronização Manual

Se preferir padronizar os domínios manualmente, siga as instruções no arquivo [DOMAIN_STANDARDIZATION.md](DOMAIN_STANDARDIZATION.md).

## Observações

- Os scripts de padronização criam arquivos com conteúdo básico que pode precisar ser adaptado para as necessidades específicas de cada domínio.
- Os arquivos existentes não são modificados, apenas os arquivos faltantes são criados.
- Após a padronização, é recomendável revisar o conteúdo dos arquivos criados para garantir que estão corretos e adequados para o domínio. 