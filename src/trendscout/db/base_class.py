from typing import Any, Dict, List, Set, Type
from sqlalchemy import MetaData
from sqlalchemy.orm import registry, DeclarativeBase, declared_attr

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)

class Base(DeclarativeBase):
    """Base class for all database models."""
    
    id: Any
    __name__: str
    metadata = metadata
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    @classmethod
    def get_dependencies(cls) -> Set[Type['Base']]:
        """Get all model dependencies for this model."""
        from sqlalchemy import inspect
        
        dependencies = set()
        mapper = inspect(cls)
        
        # Check relationships for dependencies
        for relationship in mapper.relationships:
            target = relationship.mapper.class_
            if target != cls:  # Avoid self-references
                dependencies.add(target)
        
        # Check foreign keys for dependencies
        for column in mapper.columns:
            for fk in column.foreign_keys:
                target = fk.column.table.name
                # Find the model class for this table
                for model in Base.__subclasses__():
                    if model.__tablename__ == target:
                        dependencies.add(model)
                        break
        
        return dependencies
    
    @classmethod
    def get_creation_order(cls) -> List[Type['Base']]:
        """Get the correct order of model creation based on dependencies."""
        models = Base.__subclasses__()
        ordered = []
        seen = set()
        
        def add_model(model: Type['Base']) -> None:
            if model in seen:
                return
            
            # Add dependencies first
            for dep in model.get_dependencies():
                add_model(dep)
            
            if model not in ordered:
                ordered.append(model)
                seen.add(model)
        
        # Process all models
        for model in models:
            add_model(model)
        
        return ordered
