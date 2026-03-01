# Mon Diagramme de Classe

```mermaid
classDiagram
    class Concept {
        + prefLabel : String
        + altLabel : String
    }
    class Definition {
        + text String
        + definitionType : DefinitionCategory
    }
    class Source {
        + organization : String
        + year : Integer
    }
    class TechnicalCriteria {
        + criterionName : String
        + value : Float
        + unit : String
    }

    class DefinitionCategory {
    <<enumeration>>
    ADMINISTRATIVE
    LAND_COVER
    LAND_USE
    ECOLOGICAL
}

    Concept "1" -- "1..*" Definition : has definition

    Concept "0..*" -- "0..*" Concept : broader/narrower
    
    Definition "1" -- "1" Source : provided by
    
    Definition "1..*" -- "0..*" TechnicalCriteria : quantified by