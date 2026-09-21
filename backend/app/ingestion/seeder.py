"""
Service seeder — reads services.yaml and populates the services and
service_dependencies tables on startup. Also caches the dependency
graph in Redis for fast lookups by the correlation engine.
"""

import json
import logging
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service, ServiceDependency

logger = logging.getLogger("sentinel.seeder")


def load_services_yaml(path: str) -> list[dict]:
    """Load and parse the services.yaml configuration file."""
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"services.yaml not found at {yaml_path}")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    services = data.get("services", [])
    if not services:
        raise ValueError("No services defined in services.yaml")

    logger.info(f"Loaded {len(services)} services from {yaml_path}")
    return services


async def seed_services(session: AsyncSession, services_config: list[dict]) -> dict[str, Service]:
    """
    Upsert services and their dependencies into the database.

    Returns a dict mapping service name -> Service ORM instance.
    """
    service_map: dict[str, Service] = {}

    # First pass: upsert all services
    for svc_config in services_config:
        name = svc_config["name"]
        description = svc_config.get("description", "")

        result = await session.execute(
            select(Service).where(Service.name == name)
        )
        service = result.scalar_one_or_none()

        if service is None:
            service = Service(name=name, description=description)
            session.add(service)
            logger.info(f"Created service: {name}")
        else:
            service.description = description
            logger.info(f"Service already exists: {name}")

        service_map[name] = service

    await session.flush()  # Ensure all services have IDs

    # Second pass: upsert dependencies
    for svc_config in services_config:
        name = svc_config["name"]
        deps = svc_config.get("dependencies", [])
        service = service_map[name]

        # Get existing dependencies for this service
        result = await session.execute(
            select(ServiceDependency).where(
                ServiceDependency.service_id == service.id
            )
        )
        existing_deps = {dep.depends_on_service_id for dep in result.scalars().all()}

        for dep_name in deps:
            dep_service = service_map.get(dep_name)
            if dep_service is None:
                logger.warning(
                    f"Dependency '{dep_name}' for service '{name}' "
                    f"not found in services.yaml — skipping"
                )
                continue

            if dep_service.id not in existing_deps:
                dep_link = ServiceDependency(
                    service_id=service.id,
                    depends_on_service_id=dep_service.id,
                )
                session.add(dep_link)
                logger.info(f"Created dependency: {name} -> {dep_name}")

    await session.commit()
    logger.info(f"Seeded {len(service_map)} services with dependencies")
    return service_map


async def cache_dependency_graph(redis_client, service_map: dict[str, Service], session: AsyncSession) -> None:
    """
    Cache the service dependency graph in Redis as a hash for fast lookups.
    Key: 'dependency_graph'
    Field: service_name
    Value: JSON list of dependency service names
    """
    graph = {}

    for name, service in service_map.items():
        result = await session.execute(
            select(ServiceDependency).where(
                ServiceDependency.service_id == service.id
            )
        )
        dep_links = result.scalars().all()

        dep_names = []
        for dep_link in dep_links:
            for svc_name, svc in service_map.items():
                if svc.id == dep_link.depends_on_service_id:
                    dep_names.append(svc_name)
                    break

        graph[name] = dep_names

    # Store in Redis
    pipe = redis_client.pipeline()
    await pipe.delete("dependency_graph")
    for svc_name, deps in graph.items():
        await pipe.hset("dependency_graph", svc_name, json.dumps(deps))
    await pipe.execute()

    logger.info(f"Cached dependency graph in Redis: {graph}")
