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
    DateNaissance = Column(DateType)
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
    notes = relationship("Noteeleveparmatiere", back_populates="classe_ref")

class InscriptionEleve(Base):
    __tablename__ = 'inscriptioneleve'

    id = Column(Integer, primary_key=True, nullable=False)
    Eleve = Column(Integer, ForeignKey("eleve.id"))
    Classe = Column(Integer, ForeignKey("classe.id"))
    Date = Column(DateType)
    AnneeScolaire = Column(Integer, ForeignKey("anneescolaire.id"))
    Personne = Column(Integer, ForeignKey("personne.id"))
    Modalite = Column(Integer)
    Annuler = Column(Boolean, default=False)
    DateAnnulation = Column(DateType, nullable=True)
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
    notes = relationship("Noteeleveparmatiere", back_populates="inscription_ref")

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
    idpersonne = Column(Integer, ForeignKey("personne.id"), nullable=False)
    roles = Column(String)          
    token = Column(String)
    changepassword = Column(Boolean, nullable=False, default=False)

    Personne = relationship("Personne")


class Civilite(Base):
    __tablename__ = 'civilite'

    idCivilite = Column(Integer, primary_key=True, nullable=False)
    libelleCiviliteAr = Column(String, nullable=False)
    libelleCiviliteFr = Column(String, nullable=False)


class Noteeleveparmatiere(Base):
    __tablename__ = 'noteeleveparmatiere'

    id = Column(Integer, primary_key=True, nullable=False)
    AnneeScolaire = Column(String)
    id_classe = Column(Integer, ForeignKey("classe.id"))  # Changé en Integer
    id_inscription = Column(Integer, ForeignKey("inscriptioneleve.id"))  # Changé en Integer
    id_matiere = Column(Integer, ForeignKey("matiere.id"))  # Changé en Integer
    id_trimestre = Column(Integer, ForeignKey("trimestre.id"))  # Changé en Integer
    orale = Column(String)
    TP = Column(String)
    ExamenEcrit = Column(String)
    DS = Column(String)
    DC1 = Column(String)
    DC2 = Column(String)
    nomprenom = Column(String)
    Etat = Column(String)
    EtatTP = Column(String)
    EtatExamenEcrit = Column(String)
    EtatDC1 = Column(String)
    EtatDC2 = Column(String)
    EtatDS = Column(String)
    nomprenomAr = Column(String)
    
    # Relations
    classe_ref = relationship("Classe", back_populates="notes")
    inscription_ref = relationship("InscriptionEleve", back_populates="notes")
    matiere_ref = relationship("Matiere", back_populates="notes")
    trimestre_ref = relationship("Trimestre", back_populates="notes")

class Trimestre(Base):
    __tablename__ = 'trimestre'

    id = Column(Integer, primary_key=True, nullable=False)
    nom_trimestre = Column(String)
    actif = Column(String)
    nom_trimestreAr = Column(String)
    configTrimstre = Column(Integer)
    date_debut = Column(DateType)
    date_fin = Column(DateType)

    notes = relationship("Noteeleveparmatiere", back_populates="trimestre_ref")

class Matiere(Base):
    __tablename__ = 'matiere'

    id = Column(Integer, primary_key=True, nullable=False)
    NomMatiereFr = Column(String)
    NomMatiereAr = Column(String)

    notes = relationship("Noteeleveparmatiere", back_populates="matiere_ref")

# Consultation des informations élèves
class EmploiDuTemps(Base):
    __tablename__ = 'emploidutemps'

    id = Column(Integer, primary_key=True, nullable=False)
    AnneeScolaire = Column(Integer, ForeignKey("anneescolaire.id"))
    Classe = Column(Integer, ForeignKey("classe.id"))
    Enseignant = Column(Integer, ForeignKey("enseingant.id"))
    Groupe = Column(String)
    Jour = Column(Integer, ForeignKey("jour.id"))
    Matiere = Column(Integer, ForeignKey("matiere.id"))
    Remarque = Column(String)
    Salle = Column(Integer, ForeignKey("salle.id"))
    SeanceDebut = Column(Integer, ForeignKey("seance.id"))
    SeanceFin = Column(Integer, ForeignKey("seance.id"))
    Semaine = Column(Integer, ForeignKey("semaine.id"))

    # Relations
    anneescolaire_ref = relationship("AnneeScolaire")
    classe_ref = relationship("Classe")
    enseignant_ref = relationship("Enseingant")
    jour_ref = relationship("Jour")
    matiere_ref = relationship("Matiere")
    salle_ref = relationship("Salle")
    seance_debut_ref = relationship("Seance", foreign_keys=[SeanceDebut])
    seance_fin_ref = relationship("Seance", foreign_keys=[SeanceFin])
    semaine_ref = relationship("Semaine")


class Enseingant(Base):
    __tablename__ = 'enseingant'

    id = Column(Integer, primary_key=True, nullable=False)
    banque = Column(String)
    coutHoraire = Column(Integer)
    dateDip = Column(String)
    dateNaissance = Column(DateType)
    disabled = Column(Integer)
    IdDip = Column(Integer)
    IdModPaiement = Column(Integer)
    idPersonne = Column(Integer, ForeignKey("personne.id"))
    IdQualite = Column(Integer)
    IdSituation = Column(Integer)
    lieuNaissance = Column(String)
    mail = Column(String)
    rib = Column(String)
    seuilprof = Column(Integer)
    sexe = Column(String)

    personne_ref = relationship("Personne")


class Salle(Base):
    __tablename__ = 'salle'

    id = Column(Integer, primary_key=True, nullable=False)
    codeSalleAr = Column(String)
    codeSalleFr = Column(String)
    nomSalleAr = Column(String)
    nomSalleFr = Column(String)


class Jour(Base):
    __tablename__ = 'jour'

    id = Column(Integer, primary_key=True, nullable=False)
    libelleJour = Column(String)
    libelleJourFr = Column(String)


class Semaine(Base):
    __tablename__ = 'semaine'

    id = Column(Integer, primary_key=True, nullable=False)
    libelleSemaine = Column(String)


class Groupe(Base):
    __tablename__ = 'groupe'

    id = Column(Integer, primary_key=True, nullable=False)
    libelleGroupe = Column(String)


class Seance(Base):
    __tablename__ = 'seance'

    id = Column(Integer, primary_key=True, nullable=False)
    codeSeance = Column(String)
    debut = Column(String)
    fin = Column(String)
    nomSeance = Column(String)

