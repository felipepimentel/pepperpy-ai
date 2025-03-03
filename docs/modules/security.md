# Módulo Security

O módulo `security` fornece mecanismos para proteger aplicações PepperPy, gerenciar autenticação, autorização e implementar práticas de segurança.

## Visão Geral

O módulo Security permite:

- Implementar autenticação e autorização
- Gerenciar chaves de API e credenciais de forma segura
- Aplicar políticas de segurança para LLMs e agentes
- Proteger dados sensíveis
- Auditar e monitorar atividades de segurança

## Principais Componentes

### Autenticação

```python
from pepperpy.security import (
    AuthManager,
    AuthProvider,
    UserCredentials,
    AuthToken
)

# Configurar gerenciador de autenticação
auth_manager = AuthManager(provider="oauth2")

# Autenticar usuário
credentials = UserCredentials(
    username="user@example.com",
    password="secure_password"
)
token = auth_manager.authenticate(credentials)

# Verificar token
if auth_manager.verify_token(token):
    print(f"Token válido para usuário: {token.user_id}")
    print(f"Expira em: {token.expires_at}")

# Renovar token
new_token = auth_manager.refresh_token(token)

# Revogar token
auth_manager.revoke_token(token)
```

### Autorização

```python
from pepperpy.security import (
    AuthorizationManager,
    Permission,
    Role,
    ResourcePolicy
)

# Configurar gerenciador de autorização
authz_manager = AuthorizationManager()

# Definir permissões
read_docs = Permission("read", "documents")
write_docs = Permission("write", "documents")
admin_docs = Permission("admin", "documents")

# Definir papéis (roles)
viewer_role = Role("viewer", [read_docs])
editor_role = Role("editor", [read_docs, write_docs])
admin_role = Role("admin", [read_docs, write_docs, admin_docs])

# Registrar papéis
authz_manager.register_role(viewer_role)
authz_manager.register_role(editor_role)
authz_manager.register_role(admin_role)

# Atribuir papel a um usuário
authz_manager.assign_role_to_user("user123", "editor")

# Verificar permissão
if authz_manager.has_permission("user123", "write", "documents"):
    print("Usuário pode escrever documentos")
else:
    print("Acesso negado")

# Política de recursos
doc_policy = ResourcePolicy(
    resource_type="document",
    resource_id="doc456",
    allowed_roles=["editor", "admin"],
    allowed_actions=["read", "write"]
)

# Verificar acesso a um recurso específico
if authz_manager.check_resource_access("user123", "write", "document", "doc456"):
    print("Usuário pode editar este documento")
```

### Gerenciamento de Credenciais

```python
from pepperpy.security import (
    CredentialManager,
    APIKey,
    SecretValue
)

# Criar gerenciador de credenciais
credential_manager = CredentialManager(
    storage_provider="vault",
    encryption_enabled=True
)

# Armazenar chave de API
openai_key = APIKey(
    name="openai",
    value="sk-abcdef123456",
    service="openai",
    scopes=["completions", "embeddings"]
)
credential_manager.store_api_key(openai_key)

# Recuperar chave de API
retrieved_key = credential_manager.get_api_key("openai")
print(f"API Key: {retrieved_key.value}")

# Armazenar valor secreto
db_password = SecretValue(
    name="database_password",
    value="very-secure-password"
)
credential_manager.store_secret(db_password)

# Recuperar valor secreto
password = credential_manager.get_secret("database_password")
```

### Políticas de Segurança para LLMs

```python
from pepperpy.security import (
    LLMSecurityPolicy,
    ContentFilter,
    PromptGuard,
    OutputSanitizer
)

# Criar política de segurança para LLMs
llm_policy = LLMSecurityPolicy(
    name="default_policy",
    description="Política padrão para modelos de linguagem"
)

# Configurar filtro de conteúdo
content_filter = ContentFilter(
    blocked_topics=["illegal_activities", "harmful_instructions"],
    sensitivity_level="medium",
    action="reject"  # ou "sanitize", "warn"
)
llm_policy.add_filter(content_filter)

# Configurar proteção de prompts
prompt_guard = PromptGuard(
    detect_prompt_injection=True,
    prevent_sensitive_data_leakage=True,
    max_prompt_length=4000
)
llm_policy.add_prompt_guard(prompt_guard)

# Configurar sanitizador de saída
output_sanitizer = OutputSanitizer(
    remove_pii=True,
    allowed_formats=["text", "json"],
    max_output_length=2000
)
llm_policy.add_output_sanitizer(output_sanitizer)

# Aplicar política a um modelo
from pepperpy.llm import ChatSession
chat = ChatSession(
    provider="openai",
    model="gpt-4",
    security_policy=llm_policy
)
```

### Auditoria e Monitoramento

```python
from pepperpy.security import (
    SecurityAuditor,
    AuditEvent,
    AuditLevel
)

# Criar auditor de segurança
auditor = SecurityAuditor(
    storage="database",
    connection_string="postgresql://user:password@localhost/audit_db"
)

# Registrar eventos de auditoria
auditor.log(
    AuditEvent(
        level=AuditLevel.INFO,
        event_type="authentication",
        user_id="user123",
        action="login",
        status="success",
        details={"ip": "192.168.1.1", "user_agent": "Mozilla/5.0..."}
    )
)

# Registrar evento de falha
auditor.log(
    AuditEvent(
        level=AuditLevel.WARNING,
        event_type="authorization",
        user_id="user456",
        action="access_document",
        resource_id="doc789",
        status="denied",
        details={"reason": "insufficient_permissions"}
    )
)

# Consultar eventos de auditoria
events = auditor.query(
    user_id="user123",
    event_types=["authentication", "authorization"],
    start_time="2023-01-01T00:00:00Z",
    end_time="2023-01-31T23:59:59Z",
    level=AuditLevel.WARNING
)

# Exportar relatório de auditoria
auditor.export_report(
    format="pdf",
    output_path="audit_report_jan_2023.pdf",
    start_time="2023-01-01T00:00:00Z",
    end_time="2023-01-31T23:59:59Z"
)
```

## Exemplo Completo

```python
from pepperpy.security import (
    AuthManager, 
    AuthorizationManager, 
    CredentialManager,
    LLMSecurityPolicy,
    SecurityAuditor,
    UserCredentials,
    Role,
    Permission,
    ContentFilter
)
from pepperpy.llm import ChatSession, ChatOptions

# Configurar componentes de segurança
auth_manager = AuthManager(provider="jwt")
authz_manager = AuthorizationManager()
credential_manager = CredentialManager(storage_provider="encrypted_file")
security_auditor = SecurityAuditor(storage="file", file_path="./security_logs")

# Configurar papéis e permissões
def setup_roles_and_permissions():
    # Definir permissões
    permissions = {
        "llm:basic": Permission("basic", "llm"),
        "llm:advanced": Permission("advanced", "llm"),
        "documents:read": Permission("read", "documents"),
        "documents:write": Permission("write", "documents"),
        "admin:full": Permission("full", "admin")
    }
    
    # Definir papéis
    roles = {
        "basic_user": Role("basic_user", [
            permissions["llm:basic"],
            permissions["documents:read"]
        ]),
        "premium_user": Role("premium_user", [
            permissions["llm:basic"],
            permissions["llm:advanced"],
            permissions["documents:read"],
            permissions["documents:write"]
        ]),
        "admin": Role("admin", list(permissions.values()))
    }
    
    # Registrar papéis
    for role in roles.values():
        authz_manager.register_role(role)
    
    return roles, permissions

# Configurar política de segurança para LLMs
def create_llm_security_policy(user_role):
    policy = LLMSecurityPolicy(
        name=f"{user_role}_policy",
        description=f"Política de segurança para usuários com papel {user_role}"
    )
    
    # Configurar filtros baseados no papel do usuário
    if user_role == "basic_user":
        # Política mais restritiva para usuários básicos
        content_filter = ContentFilter(
            blocked_topics=["illegal_activities", "harmful_instructions", "adult_content"],
            sensitivity_level="high",
            action="reject"
        )
        policy.add_filter(content_filter)
        policy.set_rate_limit(50, "day")  # 50 solicitações por dia
        policy.set_max_tokens(1000)
        
    elif user_role == "premium_user":
        # Política menos restritiva para usuários premium
        content_filter = ContentFilter(
            blocked_topics=["illegal_activities", "harmful_instructions"],
            sensitivity_level="medium",
            action="warn"
        )
        policy.add_filter(content_filter)
        policy.set_rate_limit(500, "day")  # 500 solicitações por dia
        policy.set_max_tokens(4000)
        
    elif user_role == "admin":
        # Política mínima para administradores
        content_filter = ContentFilter(
            blocked_topics=["illegal_activities"],
            sensitivity_level="low",
            action="log"
        )
        policy.add_filter(content_filter)
        policy.set_rate_limit(1000, "day")  # 1000 solicitações por dia
        policy.set_max_tokens(8000)
    
    return policy

# Função para autenticar usuário e configurar sessão segura
def create_secure_chat_session(username, password):
    try:
        # Autenticar usuário
        credentials = UserCredentials(username=username, password=password)
        token = auth_manager.authenticate(credentials)
        
        if not token:
            return None, "Falha na autenticação"
        
        # Obter papel do usuário
        user_id = token.user_id
        user_roles = authz_manager.get_user_roles(user_id)
        
        if not user_roles:
            return None, "Usuário sem papéis atribuídos"
        
        primary_role = user_roles[0]  # Usar o primeiro papel como principal
        
        # Verificar permissão para usar LLM
        if not authz_manager.has_permission(user_id, "basic", "llm"):
            return None, "Usuário não tem permissão para usar LLMs"
        
        # Obter credenciais para o provedor LLM
        api_key = credential_manager.get_api_key("openai")
        
        # Criar política de segurança baseada no papel
        security_policy = create_llm_security_policy(primary_role)
        
        # Determinar o modelo com base nas permissões
        model = "gpt-4" if authz_manager.has_permission(user_id, "advanced", "llm") else "gpt-3.5-turbo"
        
        # Criar sessão de chat
        chat_session = ChatSession(
            provider="openai",
            options=ChatOptions(
                model=model,
                api_key=api_key.value,
                temperature=0.7
            ),
            security_policy=security_policy
        )
        
        # Registrar evento de auditoria
        security_auditor.log(
            event_type="llm_session_created",
            user_id=user_id,
            action="create_chat_session",
            status="success",
            details={
                "model": model,
                "role": primary_role,
                "session_id": chat_session.session_id
            }
        )
        
        return chat_session, None
    
    except Exception as e:
        # Registrar falha
        security_auditor.log(
            event_type="llm_session_creation_failed",
            user_id=username,
            action="create_chat_session",
            status="failed",
            details={"error": str(e)}
        )
        return None, f"Erro ao criar sessão: {str(e)}"

# Exemplo de uso
def main():
    # Configurar papéis e permissões
    roles, permissions = setup_roles_and_permissions()
    
    # Simular cadastro de usuário
    auth_manager.register_user("alice@example.com", "secure_password", user_id="user123")
    authz_manager.assign_role_to_user("user123", "premium_user")
    
    # Armazenar chave de API
    credential_manager.store_api_key(
        name="openai",
        value="sk-your-api-key",
        service="openai"
    )
    
    # Criar sessão segura
    chat_session, error = create_secure_chat_session("alice@example.com", "secure_password")
    
    if error:
        print(f"Erro: {error}")
        return
    
    # Usar a sessão de chat
    chat_session.add_system_message("Você é um assistente seguro e útil.")
    chat_session.add_user_message("Como posso proteger minha aplicação PepperPy?")
    
    response = chat_session.generate()
    print(f"Resposta: {response.content}")
    
    # Registrar uso na auditoria
    security_auditor.log(
        event_type="llm_interaction",
        user_id="user123",
        action="generate_response",
        status="success",
        details={
            "session_id": chat_session.session_id,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
    )

if __name__ == "__main__":
    main()
```

## Configuração Avançada

```python
from pepperpy.security import (
    SecurityConfig,
    AuthConfig,
    AuthorizationConfig,
    CredentialConfig,
    AuditConfig,
    LLMSecurityConfig
)

# Configuração avançada de segurança
security_config = SecurityConfig(
    auth=AuthConfig(
        provider="oauth2",
        issuer="https://auth.example.com",
        audience="pepperpy-app",
        token_lifetime=3600,
        refresh_token_lifetime=86400,
        require_mfa=True
    ),
    authorization=AuthorizationConfig(
        provider="rbac",
        policy_enforcement="strict",
        cache_ttl=300
    ),
    credentials=CredentialConfig(
        provider="vault",
        vault_url="https://vault.example.com",
        vault_token="hvs.example-token",
        encryption_algorithm="AES-256-GCM"
    ),
    audit=AuditConfig(
        provider="database",
        connection_string="postgresql://user:password@localhost/audit_db",
        retention_days=90,
        log_level="INFO",
        include_user_data=False
    ),
    llm=LLMSecurityConfig(
        content_filtering=True,
        prompt_guarding=True,
        output_sanitization=True,
        rate_limiting=True,
        default_sensitivity="medium"
    )
)

# Inicializar componentes com configuração avançada
from pepperpy.security import SecurityManager
security_manager = SecurityManager(config=security_config)
```

## Melhores Práticas

1. **Implemente Autenticação Robusta**: Utilize métodos de autenticação fortes, como OAuth2 ou JWT, e considere a autenticação de múltiplos fatores (MFA) para maior segurança.

2. **Aplique o Princípio do Menor Privilégio**: Atribua aos usuários apenas as permissões necessárias para realizar suas tarefas.

3. **Proteja Credenciais**: Nunca armazene chaves de API ou senhas em texto simples. Utilize gerenciadores de credenciais seguros.

4. **Implemente Políticas de Segurança para LLMs**: Configure filtros de conteúdo e proteções contra injeção de prompt para evitar uso malicioso.

5. **Mantenha Registros de Auditoria**: Registre todas as atividades relacionadas à segurança para facilitar a detecção de incidentes e conformidade regulatória. 