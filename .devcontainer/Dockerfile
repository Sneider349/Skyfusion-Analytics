# Skyfusion Analytics - Dev Container
# Configuración para GitHub Codespaces con versiones consistentes de librerías geoespaciales
# Versiones fijadas: GDAL 3.6.2, Rasterio 1.3.8

FROM mcr.microsoft.com/vscode/devcontainers/python:3.10

# Metadatos del contenedor
LABEL maintainer="Skyfusion Analytics"
LABEL description="Entorno de desarrollo para análisis geoespacial"

# ============================================
# VERSIONES FIJADAS - NO MODIFICAR SIN COORDINAR
# ============================================
# GDAL: 3.6.2 (requerido por rasterio 1.3.8)
# Rasterio: 1.3.8 (última versión estable compatible)
# Python: 3.10 (largo soporte hasta 2026)
ENV GDAL_VERSION=3.6.2
ENV RASTERIO_VERSION=1.3.8

# Configuración para GDAL/rasterio
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_DATA=/usr/share/gdal
ENV PROJ_DATA=/usr/share/proj

# ============================================
# INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA
# ============================================
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        # Dependencias para GDAL/OGR
        gdal-bin=${GDAL_VERSION}* \
        libgdal-dev=${GDAL_VERSION}* \
        # Dependencias para proj
        libproj-dev \
        proj-bin \
        proj-data \
        # Dependencias para rasterio
        libgeos-dev \
        libproj-dev \
        libspatialindex-dev \
        # Herramientas de desarrollo
        git \
        curl \
        wget \
        vim \
        # Para procesamiento de imágenes
        libjpeg-dev \
        zlib1g-dev \
        libpng-dev \
        libtiff-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================
# VERIFICACIÓN DE VERSIONES DE GDAL
# ============================================
RUN gdal-config --version && echo "GDAL Version: $(gdal-config --version)" || echo "GDAL installation check failed"

# ============================================
# CREAR USUARIO NO-ROOT (Estándar Codespaces)
# ============================================
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN if [ "$USER_GID" != "1000" ] || [ "$USER_UID" != "1000" ]; then \
        groupmod --gid $USER_GID $USERNAME || true; \
        usermod --uid $USER_UID --gid $USER_GID $USERNAME || true; \
    fi

# ============================================
# INSTALACIÓN DE PYTHON Y DEPENDENCIAS
# ============================================
# Crear directorio de trabajo
WORKDIR /workspace

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt /tmp/requirements.txt

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Instalar GDAL wheel pre-compilado para la versión objetivo
RUN pip install --no-cache-dir GDAL==${GDAL_VERSION}

# Instalar rasterio con la versión fija
RUN pip install --no-cache-dir rasterio==${RASTERIO_VERSION}

# Instalar otras dependencias del proyecto
RUN if [ -f /tmp/requirements.txt ]; then \
        pip install --no-cache-dir -r /tmp/requirements.txt; \
    fi

# ============================================
# CONFIGURACIÓN DEL SHELL
# ============================================
# Agregar alias útiles
RUN echo 'alias ll="ls -la"' >> /home/${USERNAME}/.bashrc && \
    echo 'alias gs="git status"' >> /home/${USERNAME}/.bashrc && \
    echo 'export PYTHONDONTWRITEBYTECODE=1' >> /home/${USERNAME}/.bashrc

# ============================================
# VERIFICACIÓN FINAL
# ============================================
# Verificar versiones instaladas
RUN echo "=== Verificación de versiones ===" && \
    echo "GDAL: $(gdal-config --version)" && \
    python -c "import rasterio; print('Rasterio:', rasterio.__version__)" && \
    python -c "import rasterio; print('GDAL (via rasterio):', rasterio.__gdal_version__)" && \
    python -c "import numpy; print('NumPy:', numpy.__version__)" && \
    echo "=== Versiones verificadas correctamente ==="

# Cambiar a usuario no-root
USER ${USERNAME}

# Establecer directorio de trabajo
WORKDIR /workspace

# Mensaje de bienvenida
RUN echo $'\n\
╔════════════════════════════════════════════════════════════════╗\n\
║  Skyfusion Analytics - Dev Container                           ║\n\
║  GDAL: '${GDAL_VERSION}' | Rasterio: '${RASTERIO_VERSION}'                        ║\n\
╚════════════════════════════════════════════════════════════════╝\n' | cat
