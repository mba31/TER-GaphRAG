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
  +String id
  +String text
  +String type
}

class Source {
  +String uri
  +String name
  +Integer year
  +List<String> url
}

class GeographicZone {
  +String uri
  +String geoZoneName
}

class Country {
  +String CountryName
  +List<Enum> officialLangages 
}

class Organization {
  +String OrganizationName
  +List Members
}

class TechnicalCriteria {
  +String uri
  +String criterionName
  +Float value
  +String unit
}

class ConceptRelation {
  +String uri
  +String relationType
}

Concept "1" --> "0..*" Definition : HAS_DEFINITION
Source "1" --> "0..*" Definition : PROVIDED_BY
Definition "0..*" --> "0..*" GeographicZone : APPLIES_TO
Definition "1" --> "0..*" TechnicalCriteria : QUANTIFIED_BY
GeographicZone <|-- Organization
Organization <|-- Country 
GeographicZone "0..*" --o Organization : IS_MEMBER_OF

Concept "1" --> "0..*" ConceptRelation : sourceConcept
ConceptRelation "0..*" --> "1" Concept : targetConcept
