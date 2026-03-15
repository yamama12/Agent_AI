from sqlalchemy import Column, Integer, String, Date as DateType, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from database.db import Base


class Personne(Base):
    __tablename__ = 'personne'

    id = Column(Integer, primary_key=True, nullable=False)
    NomFr = Column(String(255))
    PrenomFr = Column(String(255))
    NomAr = Column(String(255))
    PrenomAr = Column(String(255))
    Cin = Column(String(50))
    CinLiv = Column(String(50))
    AdresseFr = Column(String(255))
    AdresseAr = Column(String(255))
    Tel1 = Column(String(50))
    Tel2 = Column(String(50))
    Tel3 = Column(String(50))
    Email = Column(String(255))
    Login = Column(String(255))
    Pwd = Column(String(255))
    Nationalite = Column(Integer)
    Localite = Column(Integer)
    Civilite = Column(Integer)
    codepostal = Column(String(50))
    SoldeCantineParJour = Column(Float)
    type = Column(String(50))
    nationaliteAutre = Column(String(255))
    localiteAutre = Column(String(255))

    # Relations
    eleves = relationship("Eleve", back_populates="personne")
    inscriptions = relationship("InscriptionEleve", back_populates="personne")


class Eleve(Base):
    __tablename__ = 'eleve'

    id = Column(Integer, primary_key=True, nullable=False)
    DateNaissance = Column(DateType())
    LieuNaissance = Column(String(255))
    IdPersonne = Column(Integer, ForeignKey("personne.id"))
    Solde = Column(Float)
    photo = Column(String(255))
    IdEdusrv = Column(String(50))
    AutreLieuNaissance = Column(String(255))

    personne = relationship("Personne", back_populates="eleves")
    inscriptions = relationship("InscriptionEleve", back_populates="eleve")


class AnneeScolaire(Base):
    __tablename__ = 'anneescolaire'

    id = Column(Integer, primary_key=True, nullable=False)
    AnneeScolaire = Column(String(50))
    Actif = Column(Boolean)
    AnneeScolaireAr = Column(String(50))
    Annee = Column(String(50))
    AnneePreinscription = Column(Integer)
    actifmobile = Column(Boolean)
    
    inscriptions = relationship("InscriptionEleve", back_populates="anneescolaire")


class Classe(Base):
    __tablename__ = 'classe'

    id = Column(Integer, primary_key=True, nullable=False)
    CODECLASSEAR = Column(String(50))
    CODECLASSEFR = Column(String(50))
    ID_ANNEE_SCO = Column(Integer, ForeignKey("anneescolaire.id"), nullable=False)
    NOMCLASSEAR = Column(String(50))
    NOMCLASSEFR = Column(String(50))
    ordre = Column(Integer, nullable=False)

    inscriptions = relationship("InscriptionEleve", back_populates="classe")


class InscriptionEleve(Base):
    __tablename__ = 'inscriptioneleve'

    id = Column(Integer, primary_key=True, nullable=False)
    Eleve = Column(Integer, ForeignKey("eleve.id"))
    Classe = Column(Integer, ForeignKey("classe.id"))
    Date = Column(DateType())
    AnneeScolaire = Column(Integer, ForeignKey("anneescolaire.id"))
    Personne = Column(Integer, ForeignKey("personne.id"))
    Modalite = Column(Integer)
    Annuler = Column(Boolean, default=False)
    DateAnnulation = Column(DateType(), nullable=True)
    groupe = Column(Integer)
    PreinscriptionId = Column(Integer, nullable=True)
    Restant_Scolaire = Column(Float, nullable=False)
    Solde = Column(Float, nullable=False)
    TTC_Scolaire = Column(Float, nullable=False)
    TypeInscri = Column(String(50))

    eleve = relationship("Eleve", back_populates="inscriptions")
    anneescolaire = relationship("AnneeScolaire", back_populates="inscriptions")
    personne = relationship("Personne", back_populates="inscriptions")
    classe = relationship("Classe", back_populates="inscriptions")


class Localite(Base):
    __tablename__ = 'localite'

    IDLOCALITE = Column(Integer, primary_key=True, nullable=False)
    CODEDELEGATION = Column(Integer)
    LIBELLELOCALITEFR = Column(String)
    LIBELLELOCALITEAR = Column(String)
    CODEPOSTAL = Column(String)


class Nationalite(Base):
    __tablename__ = 'nationalite'

    id = Column(Integer, primary_key=True, nullable=False)
    NationaliteFr = Column(String)
    NationaliteAr = Column(String)

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    idpersonne = Column(Integer, nullable=False)
    roles = Column(String)          
    token = Column(String)
    changepassword = Column(String, nullable=False) 


class Civilite(Base):
    __tablename__ = 'civilite'

    idCivilite = Column(Integer, primary_key=True, nullable=False)
    libelleCiviliteAr = Column(String, nullable=False)
    libelleCiviliteFr = Column(String, nullable=False)





