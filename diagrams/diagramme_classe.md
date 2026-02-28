# Mon Diagramme de Classe

```mermaid
classDiagram
    class Concept {
        +String prefLabel
        +String altLabel
    }
    class Definition {
        +String text
        +String typeInterpretation
    }
    class Source {
        +String organization
        +Integer year
    }
    class TechnicalCriteria {
        +Float minHeight
        +Float minCanopyCover
    }

    Concept "1" -- "0..*" Definition : has definition
    Definition "1" -- "1" Source : provided by
    Definition "0..1" -- "0..*" TechnicalCriteria : quantified by