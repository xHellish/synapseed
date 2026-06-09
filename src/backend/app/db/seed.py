"""Script de seed para cargar datos del SFE, distribuidores y regulaciones en la DB."""

from __future__ import annotations

import asyncio
import csv
import os
from pathlib import Path
from typing import Any

import numpy as np
from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import (
    Distributor,
    Product,
    ProductCategory,
    ProductDistributor,
    ProductStatus,
    Regulation,
    RegulationType,
)


# Configuración
OUTPUT_DIR = Path("../../output")  # Relativo a src/backend (project root/output)
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768
BATCH_SIZE = 100

# Inicializar cliente Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None


async def get_embedding(text: str) -> list[float] | None:
    """Genera embedding usando Gemini text-embedding-004."""
    if not text or not text.strip():
        return None
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        # gemini devuelve una lista de embeddings
        embedding = response.embeddings[0].values
        if len(embedding) == EMBEDDING_DIM:
            return embedding
        else:
            # Ajustar dimensión si es necesario
            if len(embedding) > EMBEDDING_DIM:
                return embedding[:EMBEDDING_DIM]
            else:
                return embedding + [0.0] * (EMBEDDING_DIM - len(embedding))
    except Exception as e:
        print(f"  [WARN] Error generando embedding: {e}")
        return None


async def seed_products(session: AsyncSession, csv_path: Path) -> int:
    """Carga productos desde plaguicidas.csv y fertilizantes.csv."""
    print(f"\n📦 Cargando productos desde {csv_path}...")
    
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Determinar categoría por nombre del archivo
            categoria = "plaguicida" if "plaguicidas" in str(csv_path) else "fertilizante"
            
            # Estado del registro
            estado = row.get("estado", "").lower()
            if estado == "activo":
                estado_valor = "ACTIVO"
            elif estado == "cancelado":
                estado_valor = "CANCELADO"
            elif estado == "expirado":
                estado_valor = "EXPIRADO"
            elif estado == "suspendido":
                estado_valor = "SUSPENDIDO"
            else:
                estado_valor = "ACTIVO"
            
            # Crear texto para embedding
            embedding_text = f"{row.get('nombre_comercial') or row.get('marca', '')} {row.get('ingredientes', '')} {categoria}"
            
            product = Product(
                numero_registro=row.get("numero_registro", "").strip(),
                nombre_comercial=row.get("marca", "").strip() if "plaguicidas" in str(csv_path) else row.get("marca", "").strip(),
                ingrediente_activo=row.get("ingredientes", "").strip(),
                categoria=ProductCategory[categoria.upper()],
                estado=ProductStatus[estado_valor],
                banda_toxicologica=None,  # Se podrá agregar después
                registrante=row.get("registrante", "").strip() if "registrante" in row else None,
                dosis_recomendada=None,
                intervalo_seguridad_dias=None,
                precio_referencia_por_litro=None,
                cultivo_objetivo=None,
                problema_objetivo=None,
                embedding=None,  # Se llenará en batch separado
            )
            
            # Usar upsert: insert si no existe, update si existe
            existing = await session.execute(
                select(Product).where(Product.numero_registro == product.numero_registro)
            )
            existing_product = existing.scalar_one_or_none()
            
            if existing_product:
                # Actualizar campos
                existing_product.nombre_comercial = product.nombre_comercial
                existing_product.ingrediente_activo = product.ingrediente_activo
                existing_product.categoria = product.categoria
                existing_product.estado = product.estado
                existing_product.registrante = product.registrante
            else:
                session.add(product)
            
            count += 1
            if count % BATCH_SIZE == 0:
                await session.flush()
                print(f"  Procesados: {count}")
    
    await session.flush()
    print(f"  ✅ Total productos cargados/actualizados: {count}")
    return count


async def seed_distributors(session: AsyncSession) -> int:
    """Crea distribuidores de ejemplo basados en los registrantes del SFE."""
    print("\n🏢 Creando distribuidores...")
    
    # Obtener registrantes únicos de productos
    result = await session.execute(
        select(Product.registrante).where(Product.registrante.is_not(None)).distinct()
    )
    registrantes = [r[0] for r in result.fetchall() if r[0]]
    
    # Distribuidores principales de Costa Rica (basados en registrantes reales)
    distributors_data = [
        {"nombre": "UPL Costa Rica S.A.", "correo": "ventas@upl.com", "telefono": "+506 2283-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "San José", "distrito": "Carmen"},
        {"nombre": "Adama Crop Solutions ACC S.A.", "correo": "info@adama.com", "telefono": "+506 2290-XXXX", "ubicacion": "Alajuela", "provincia": "Alajuela", "canton": "Alajuela", "distrito": "San Rafael"},
        {"nombre": "Corteva Agriscience Costa Rica S.A.", "correo": "corteva.cr@corteva.com", "telefono": "+506 2282-XXXX", "ubicacion": "Heredia", "provincia": "Heredia", "canton": "Heredia", "distrito": "Mercedes"},
        {"nombre": "Basf Costa Rica S.A.", "correo": "basf.cr@basf.com", "telefono": "+506 2293-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Escazú", "distrito": "San Rafael"},
        {"nombre": "Syngenta Costa Rica S.A.", "correo": "syngenta.cr@syngenta.com", "telefono": "+506 2283-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Santa Ana", "distrito": "Pozos"},
        {"nombre": "Bayer Costa Rica S.A.", "correo": "bayer.cr@bayer.com", "telefono": "+506 2284-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Curridabat", "distrito": "Granadilla"},
        {"nombre": "FMC Química Costa Rica S.A.", "correo": "fmc.cr@fmc.com", "telefono": "+506 2291-XXXX", "ubicacion": "Alajuela", "provincia": "Alajuela", "canton": "Grecia", "distrito": "San Isidro"},
        {"nombre": "Nufarm Costa Rica S.A.", "correo": "nufarm.cr@nufarm.com", "telefono": "+506 2285-XXXX", "ubicacion": "Cartago", "provincia": "Cartago", "canton": "Cartago", "distrito": "Oriental"},
        {"nombre": "Sumitomo Chemical Costa Rica S.A.", "correo": "sumitomo.cr@sumitomo.com", "telefono": "+506 2286-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Moravia", "distrito": "San Vicente"},
        {"nombre": "Personna de Costa Rica S.A.", "correo": "personna@personna.co.cr", "telefono": "+506 2287-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Desamparados", "distrito": "San Antonio"},
        {"nombre": "Bio Control S.A.", "correo": "biocontrol@biocontrol.co.cr", "telefono": "+506 2288-XXXX", "ubicacion": "Alajuela", "provincia": "Alajuela", "canton": "Zarcero", "distrito": "Zarcero"},
        {"nombre": "Importadora Agr Lag Limitada", "correo": "lag@lag.co.cr", "telefono": "+506 2289-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Alajuelita", "distrito": "San Josecito"},
        {"nombre": "Supliagro World Connection S.R.L.", "correo": "supliagro@supliagro.com", "telefono": "+506 2290-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Aserrí", "distrito": "Aserrí"},
        {"nombre": "Distribuidora Comercial Agrotico S.A.", "correo": "agrotico@agrotico.com", "telefono": "+506 2292-XXXX", "ubicacion": "Cartago", "provincia": "Cartago", "canton": "Paraíso", "distrito": "Paraíso"},
        {"nombre": "Cosmoagro S.A.", "correo": "cosmoagro@cosmoagro.com", "telefono": "+506 2293-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Turrubares", "distrito": "San Pedro"},
        {"nombre": "Grisco S.A.", "correo": "griscom@griscom.co.cr", "telefono": "+506 2294-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Puriscal", "distrito": "Santiago"},
        {"nombre": "Distribuidora Agro Comercial S.A.", "correo": "dac@dac.co.cr", "telefono": "+506 2295-XXXX", "ubicacion": "Guanacaste", "provincia": "Guanacaste", "canton": "Liberia", "distrito": "Liberia"},
        {"nombre": "Abonos del Pacifico S.A.", "correo": "abonospacifico@ap.co.cr", "telefono": "+506 2296-XXXX", "ubicacion": "Puntarenas", "provincia": "Puntarenas", "canton": "Puntarenas", "distrito": "Puntarenas"},
        {"nombre": "Formulaciones Quimicas S.A.", "correo": "formuquisa@formuquisa.com", "telefono": "+506 2297-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Acosta", "distrito": "San Ignacio"},
        {"nombre": "La Casa del Agricultor S.A. (Casagri)", "correo": "casagri@casagri.co.cr", "telefono": "+506 2298-XXXX", "ubicacion": "San José", "provincia": "San José", "canton": "Coronado", "distrito": "San Isidro"},
    ]
    
    count = 0
    for d_data in distributors_data:
        existing = await session.execute(
            select(Distributor).where(Distributor.nombre == d_data["nombre"])
        )
        if not existing.scalar_one_or_none():
            distributor = Distributor(**d_data)
            session.add(distributor)
            count += 1
    
    # Agregar registrantes que no estén en la lista
    existing_names = {d["nombre"] for d in distributors_data}
    for reg in registrantes:
        if reg and reg not in existing_names:
            existing = await session.execute(
                select(Distributor).where(Distributor.nombre == reg)
            )
            if not existing.scalar_one_or_none():
                distributor = Distributor(
                    nombre=reg,
                    correo=None,
                    telefono=None,
                    ubicacion=None,
                    provincia=None,
                    canton=None,
                    distrito=None,
                )
                session.add(distributor)
                count += 1
    
    await session.flush()
    print(f"  ✅ Total distribuidores creados: {count}")
    return count


async def link_products_distributors(session: AsyncSession) -> int:
    """Vincula productos con distribuidores basándose en el campo registrante."""
    print("\n🔗 Vinculando productos con distribuidores...")
    
    # Obtener todos los productos con registrante
    result = await session.execute(
        select(Product).where(Product.registrante.is_not(None))
    )
    products = result.scalars().all()
    
    # Obtener todos los distribuidores
    result = await session.execute(select(Distributor))
    distributors = {d.nombre: d for d in result.scalars().all()}
    
    count = 0
    for product in products:
        if product.registrante and product.registrante in distributors:
            distributor = distributors[product.registrante]
            
            # Verificar si ya existe la relación
            existing = await session.execute(
                select(ProductDistributor).where(
                    ProductDistributor.product_id == product.id,
                    ProductDistributor.distributor_id == distributor.id
                )
            )
            if not existing.scalar_one_or_none():
                link = ProductDistributor(
                    product_id=product.id,
                    distributor_id=distributor.id
                )
                session.add(link)
                count += 1
    
    await session.flush()
    print(f"  ✅ Total vínculos creados: {count}")
    return count


async def seed_regulations(session: AsyncSession) -> int:
    """Crea regulaciones base del MAG/SFE."""
    print("\n📋 Cargando regulaciones...")
    
    regulations_data = [
        {
            "numero": "Decreto 32997-MAG-S",
            "titulo": "Reglamento para el Registro, Uso y Control de Plaguicidas",
            "tipo": RegulationType.DECRETO,
            "fecha_publicacion": "2006-06-16",
            "fuente_url": "https://www.sfe.go.cr/sites/default/files/decreto_32997.pdf",
            "resumen": "Establece los requisitos para el registro, importación, fabricación, exportación, distribución y uso de plaguicidas en Costa Rica.",
            "contenido_completo": "",
            "sustancias_afectadas": "Todos los ingredientes activos de plaguicidas",
            "cultivos_afectados": "Todos",
        },
        {
            "numero": "Decreto 33697-MAG-S",
            "titulo": "Reglamento para el Registro, Control y Uso de Fertilizantes",
            "tipo": RegulationType.DECRETO,
            "fecha_publicacion": "2007-02-16",
            "fuente_url": "https://www.sfe.go.cr/sites/default/files/decreto_33697.pdf",
            "resumen": "Regula el registro, importación, fabricación, distribución y uso de fertilizantes en Costa Rica.",
            "contenido_completo": "",
            "sustancias_afectadas": "Componentes de fertilizantes (N, P, K, micronutrientes)",
            "cultivos_afectados": "Todos",
        },
        {
            "numero": "Ley 7664",
            "titulo": "Ley de Registro, Control y Uso de Plaguicidas",
            "tipo": RegulationType.LEY,
            "fecha_publicacion": "1997-04-30",
            "fuente_url": "https://www.sfe.go.cr/sites/default/files/ley_7664.pdf",
            "resumen": "Ley marco que regula la importación, fabricación, distribución, venta y uso de plaguicidas.",
            "contenido_completo": "",
            "sustancias_afectadas": "Ingredientes activos prohibidos/restringidos",
            "cultivos_afectados": "Todos",
        },
        {
            "numero": "Lista Prohibida SFE 2024",
            "titulo": "Lista de Sustancias Prohibidas y Restringidas por el SFE",
            "tipo": RegulationType.LISTA_PROHIBIDA,
            "fecha_publicacion": "2024-01-15",
            "fuente_url": "https://www.sfe.go.cr/lista-prohibida",
            "resumen": "Lista actualizada de ingredientes activos prohibidos y con restricciones de uso en Costa Rica.",
            "contenido_completo": "",
            "sustancias_afectadas": "Endosulfán, DDT, Aldrín, Dieldrín, Heptacloro, Clordano, Mirex, Toxafeno, Hexaclorobenceno, Parationa metílica, Monocrofos, Fosfamidón, Metamidofos, Triclorfon",
            "cultivos_afectados": "Todos",
        },
        {
            "numero": "Norma Nacional LMR",
            "titulo": "Norma Nacional de Límites Máximos de Residuos (LMR) de Plaguicidas",
            "tipo": RegulationType.LMR,
            "fecha_publicacion": "2023-06-01",
            "fuente_url": "https://www.sfe.go.cr/lmr",
            "resumen": "Establece los límites máximos de residuos de plaguicidas permitidos en productos agrícolas.",
            "contenido_completo": "",
            "sustancias_afectadas": "Todos los plaguicidas con LMR establecido",
            "cultivos_afectados": "Todos los cultivos con LMR",
        },
    ]
    
    count = 0
    for reg_data in regulations_data:
        existing = await session.execute(
            select(Regulation).where(Regulation.numero == reg_data["numero"])
        )
        if not existing.scalar_one_or_none():
            regulation = Regulation(**reg_data, embedding=None)
            session.add(regulation)
            count += 1
    
    await session.flush()
    print(f"  ✅ Total regulaciones creadas: {count}")
    return count


async def generate_embeddings(session: AsyncSession) -> None:
    """Genera embeddings vectoriales para productos y regulaciones."""
    print("\n🧠 Generando embeddings vectoriales...")
    
    # Embeddings para productos
    result = await session.execute(
        select(Product).where(Product.embedding.is_(None))
    )
    products = result.scalars().all()
    print(f"  Productos sin embedding: {len(products)}")
    
    for i, product in enumerate(products):
        text = f"{product.nombre_comercial} {product.ingrediente_activo} {product.categoria.value} para {product.cultivo_objetivo or 'uso general'}"
        embedding = await get_embedding(text)
        if embedding:
            product.embedding = embedding
        
        if i % 50 == 0:
            await session.flush()
            print(f"  Procesados: {i}/{len(products)}")
    
    await session.flush()
    print(f"  ✅ Embeddings de productos generados")
    
    # Embeddings para regulaciones
    result = await session.execute(
        select(Regulation).where(Regulation.embedding.is_(None))
    )
    regulations = result.scalars().all()
    print(f"  Regulaciones sin embedding: {len(regulations)}")
    
    for i, regulation in enumerate(regulations):
        text = f"{regulation.titulo} {regulation.resumen or ''} {regulation.sustancias_afectadas or ''}"
        embedding = await get_embedding(text)
        if embedding:
            regulation.embedding = embedding
        
        if i % 10 == 0:
            await session.flush()
            print(f"  Procesados: {i}/{len(regulations)}")
    
    await session.flush()
    print(f"  ✅ Embeddings de regulaciones generados")


async def main():
    """Función principal de seed."""
    print("=" * 60)
    print(" SynapSeed - Seed de Base de Datos")
    print("=" * 60)
    
    # Verificar API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY no configurada. Los embeddings no se generarán.")
    
    async with get_db_session() as session:
        # 1. Cargar productos (plaguicidas)
        plaguicidas_path = OUTPUT_DIR / "plaguicidas.csv"
        if plaguicidas_path.exists():
            await seed_products(session, plaguicidas_path)
        else:
            print(f"  ⚠️  No se encontró {plaguicidas_path}")
        
        # 2. Cargar productos (fertilizantes)
        fertilizantes_path = OUTPUT_DIR / "fertilizantes.csv"
        if fertilizantes_path.exists():
            await seed_products(session, fertilizantes_path)
        else:
            print(f"  ⚠️  No se encontró {fertilizantes_path}")
        
        # 3. Crear distribuidores
        await seed_distributors(session)
        
        # 4. Vincular productos con distribuidores
        await link_products_distributors(session)
        
        # 5. Cargar regulaciones
        await seed_regulations(session)
        
        # 6. Generar embeddings (si hay API key)
        if os.getenv("GEMINI_API_KEY"):
            await generate_embeddings(session)
        else:
            print("\n⚠️  Saltando generación de embeddings (no hay GEMINI_API_KEY)")
        
        # Commit all changes
        await session.commit()
        
        print("\n" + "=" * 60)
        print(" ✅ Seed completado exitosamente")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())