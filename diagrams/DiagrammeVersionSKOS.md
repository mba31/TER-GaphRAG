# Mon Diagramme de Classe

```mermaid
classDiagram

class Concept {
  +String uri
  +String prefLabel
  +List~String~ altLabels
}

class Definition {
  +String uri
  +String text
}

class Source {
  +String uri
  +String name
  +String organization
  +String country
  +Integer year
  +String url
}

class GeographicZone {
  +String uri
  +String name
}

class TechnicalCriterion {
  +String uri
  +String criterionName
  +Float value
  +String unit
}

Concept --> Definition : "ex_hasDefinition"
Definition --> Source : "dcterms_source"
Definition --> GeographicZone : "ex_appliesTo"

Definition --> TechnicalCriterion : "ex_hasCriterion"

Concept --> Concept : "skos_broader"
Concept --> Concept : "skos_narrower"
Concept --> Concept : "skos_related"