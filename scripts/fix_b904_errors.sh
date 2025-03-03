#!/bin/bash
# Script para corrigir erros B904 (exceções sem from err ou from None)

# Corrigir pepperpy/analysis/code.py
sed -i '257s/raise ProcessingError(f"Code transformation failed: {str(e)}")/raise ProcessingError(f"Code transformation failed: {str(e)}") from e/' pepperpy/analysis/code.py

# Corrigir pepperpy/caching/distributed.py
sed -i '128s/raise BackendError(f"Failed to get value from Redis: {e}")/raise BackendError(f"Failed to get value from Redis: {e}") from e/' pepperpy/caching/distributed.py
sed -i '175s/raise BackendError(f"Failed to delete value from Redis: {e}")/raise BackendError(f"Failed to delete value from Redis: {e}") from e/' pepperpy/caching/distributed.py
sed -i '335s/raise BackendError(f"Failed to get TTL from Redis: {e}")/raise BackendError(f"Failed to get TTL from Redis: {e}") from e/' pepperpy/caching/distributed.py

echo "Erros B904 corrigidos nos arquivos:"
echo "- pepperpy/analysis/code.py"
echo "- pepperpy/caching/distributed.py" 