# Modèle SKOS basé sur le Diagramme de Classe

Ce document décrit la traduction en SKOS du diagramme de classes fourni, représenté en RDF Turtle.

---

## Préfixes
```turtle
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.org/schema#> .
@prefix geo: <http://www.opengis.net/ont/geosparql#> .

ex:Concept a rdfs:Class ;
    rdfs:subClassOf skos:Concept ;
    rdfs:label "Concept"@en .

ex:Definition a rdfs:Class ;
    rdfs:label "Definition"@en .

ex:Source a rdfs:Class ;
    rdfs:label "Source"@en .

ex:GeographicZone a rdfs:Class ;
    rdfs:label "Geographic Zone"@en .

ex:Country a rdfs:Class ;
    rdfs:subClassOf ex:GeographicZone ;
    rdfs:label "Country"@en .

ex:Organization a rdfs:Class ;
    rdfs:subClassOf ex:GeographicZone ;
    rdfs:label "Organization"@en .

ex:TechnicalCriteria a rdfs:Class ;
    rdfs:label "Technical Criteria"@en .

ex:ConceptRelation a rdfs:Class ;
    rdfs:label "Concept Relation"@en .


# Propriétés SKOS
skos:prefLabel a rdf:Property .
skos:altLabel a rdf:Property .
skos:broader a rdf:Property .
skos:narrower a rdf:Property .
skos:related a rdf:Property .

# Extensions personnalisées basées sur le diagramme
ex:hasDefinition a rdf:Property ;
    rdfs:domain ex:Concept ;
    rdfs:range ex:Definition ;
    rdfs:label "has definition"@en .

ex:providedBy a rdf:Property ;
    rdfs:domain ex:Definition ;
    rdfs:range ex:Source ;
    rdfs:label "provided by"@en .

ex:appliesTo a rdf:Property ;
    rdfs:domain ex:Definition ;
    rdfs:range ex:GeographicZone ;
    rdfs:label "applies to"@en .

ex:quantifiedBy a rdf:Property ;
    rdfs:domain ex:Definition ;
    rdfs:range ex:TechnicalCriteria ;
    rdfs:label "quantified by"@en .

ex:isMemberOf a rdf:Property ;
    rdfs:domain ex:GeographicZone ;
    rdfs:range ex:Organization ;
    rdfs:label "is member of"@en .

ex:sourceConcept a rdf:Property ;
    rdfs:domain ex:ConceptRelation ;
    rdfs:range ex:Concept ;
    rdfs:label "source concept"@en .

ex:targetConcept a rdf:Property ;
    rdfs:domain ex:ConceptRelation ;
    rdfs:range ex:Concept ;
    rdfs:label "target concept"@en .
