#!/usr/bin/env python3
"""
Utility functions for PII detection.
"""

from typing import List
from pii_entity import PIIEntity

def deduplicate_entities(entities: List[PIIEntity]) -> List[PIIEntity]:
    """
    Remove duplicate and overlapping entities.
    
    Args:
        entities: List of detected entities
        
    Returns:
        Deduplicated list, keeping highest confidence entities
    """
    if not entities:
        return []
    
    # Sort by start position
    sorted_entities = sorted(entities, key=lambda x: x.start_pos)
    
    deduplicated = []
    for entity in sorted_entities:
        # Check for overlap with existing entities
        overlaps = False
        for i, existing in enumerate(deduplicated):
            if entities_overlap(entity, existing):
                # Overlap detected - keep the one with higher confidence
                if entity.confidence > existing.confidence:
                    deduplicated[i] = entity
                overlaps = True
                break
        
        if not overlaps:
            deduplicated.append(entity)
    
    return sorted(deduplicated, key=lambda x: x.start_pos)

def entities_overlap(entity1: PIIEntity, entity2: PIIEntity) -> bool:
    """
    Check if two entities overlap in text position.
    
    Args:
        entity1: First entity
        entity2: Second entity
        
    Returns:
        True if entities overlap
    """
    return (entity1.start_pos < entity2.end_pos and 
            entity1.end_pos > entity2.start_pos)

def merge_entity_lists(*entity_lists: List[PIIEntity]) -> List[PIIEntity]:
    """
    Merge multiple lists of entities and deduplicate.
    
    Args:
        *entity_lists: Variable number of entity lists
        
    Returns:
        Merged and deduplicated list
    """
    all_entities = []
    for entity_list in entity_lists:
        all_entities.extend(entity_list)
    
    return deduplicate_entities(all_entities)