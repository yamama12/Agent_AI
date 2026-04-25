from fastapi import FastAPI
from api import personnes, eleves, inscriptionsEleves, classes, anneeScolaire, chat,documents, localites, auth, graph, civilite, user, matiere, noteeleveparmatiere, trimestre
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Agent IA Backend")

app.include_router(personnes.router)
app.include_router(eleves.router)
app.include_router(inscriptionsEleves.router)
app.include_router(classes.router)
app.include_router(anneeScolaire.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(graph.router)
app.include_router(localites.router)
app.include_router(civilite.router)
app.include_router(trimestre.router)
app.include_router(matiere.router)
app.include_router(noteeleveparmatiere.router)


app.include_router(auth.router)
app.include_router(user.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory="files"), name="files")
app.mount("/statistics", StaticFiles(directory="statistics"), name="statistics")

@app.get("/")
async def root():
    return {"message": "Backend bd_eduise opérationnel"}

