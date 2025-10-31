import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd


# Promgramme de envoye de singnal

# === Saisie du message ===
message = input("Saisissez votre message : ")

# Conversion du message en binaire (chaque caractère codé sur 7 bits)
binary_message = ''.join(format(ord(char), '07b') for char in message)
print(binary_message)

# === Paramètres du signal ===
Fe = 41000  # Fréquence d'échantillonnage (Hz)
Fp = 2000   # Fréquence de la porteuse (Hz)
baud = 300  # Débit binaire (bits/s)
Nbits = len(binary_message) * 2  # Chaque bit devient deux symboles en Manchester
Ns = int(Fe / baud)  # Nombre d'échantillons par bit
N = Ns * Nbits       # Nombre total d'échantillons
D = N / Fe           # Durée totale du signal

# === Codage Manchester ===
manchester_thomas = []
for bit in binary_message:
    if bit == '1':
        manchester_thomas.extend([1, 0])  # 1 → 10
    else:
        manchester_thomas.extend([0, 1])  # 0 → 01

print(manchester_thomas)

# Duplication du signal pour adapter la longueur à la fréquence d'échantillonnage
Binaire_duplique = np.repeat(manchester_thomas, Ns)

# === Fonction de modulation ASK ===
def modulation_ASK(Binaire_duplique, Fe=41000, Fp=2000, Ap=1):
    """Modulation Amplitude Shift Keying (ASK)"""
    # Création du vecteur temps
    t = np.arange(0, len(Binaire_duplique) / Fe, 1 / Fe)

    # Ajustement des tailles (sécurité)
    min_length = min(len(t), len(Binaire_duplique))
    t = t[:min_length]
    Binaire_duplique = Binaire_duplique[:min_length]

    # Génération de la porteuse
    Porteuse = Ap * np.sin(2 * np.pi * Fp * t)

    # Modulation par multiplication
    ASK = Binaire_duplique * Porteuse

    return ASK, t

# === Fonction de modulation FSK ===
def modulation_FSK(Binaire_duplique, Fe=41000, Fp0=2000, Fp1=2500):
    """Modulation Frequency Shift Keying (FSK)"""
    t = np.arange(0, len(Binaire_duplique) / Fe, 1 / Fe)

    # Ajustement des tailles
    min_length = min(len(t), len(Binaire_duplique))
    t = t[:min_length]
    Binaire_duplique = Binaire_duplique[:min_length]

    # Génération du signal FSK : fréquence différente selon le bit
    FSK = np.where(Binaire_duplique == 1,
                   np.sin(2 * np.pi * Fp1 * t),
                   np.sin(2 * np.pi * Fp0 * t))
    return FSK, t

# === Choix de la modulation ===
Modulation = input("Saisissez votre modulation (ASK ou FSK) : ")

if Modulation == "ASK":
    signal_mod, temps = modulation_ASK(Binaire_duplique)
    plt.plot(temps, signal_mod, label="Signal ASK", color='red')

elif Modulation == "FSK":
    signal_mod, temps = modulation_FSK(Binaire_duplique)
    plt.plot(temps, signal_mod, label="Signal FSK", color='blue')

else:
    print("Cette modulation n'existe pas.")
    exit()

# === Envoi du signal audio ===
sd.play(signal_mod, Fe)
sd.wait()


# Promgramme pour reçevoir le singnal

# === Démodulation ASK ===

def demodulation_ASK() :
    # Paramètres du signal
    N_ASK = len(modulation_ASK(Binaire_duplique, Fe=41000, Fp=2000, Ap=1)[0])  # Nombre total d'échantillons
    D = N_ASK / Fe  # Durée totale du signal
    # Vecteur temps
    t = np.linspace(0, D, N_ASK)  

    # Porteuse
    Porteuse = np.sin(2 * np.pi * Fp * t)

    # Produit du signal reçu avec la porteuse
    Produit = modulation_ASK(Binaire_duplique, Fe=41000, Fp=2000, Ap=1)[0] * Porteuse

    # Intégration pour la démodulation
    y = []  # Résultat de l'intégration
    for i in range(0, N_ASK, Ns):
        y.append(np.trapz(Produit[i:i + Ns], t[i:i + Ns]))

    # Seuil pour récupérer les bits
    seuil = max(y) / 2  # On prend la moitié du maximum comme seuil
    bits_chiffre = [1 if val > seuil else 0 for val in y]

    return bits_chiffre


# === Démodulation FSK ===

def demodulation_FSK():# Paramètres
    N_FSK = len(FSK)  # Nombre total d'échantillons
    D_FSK = N_FSK / Fe  # Durée totale du signal

    Ns = int(Fe / baud)  # Nombre d'échantillons par bit

    # Signal reçu (exemple : remplacer par ton signal FSK reçu)
    t_FSK = np.arange(0, D_FSK , N_FSK)


    # Génération des porteuses pour la démodulation
    Porteuse_0 = np.sin(2 * np.pi * Fp0 * t)
    Porteuse_1 = np.sin(2 * np.pi * Fp1 * t)

    # Produit du signal reçu avec les deux porteuses
    Produit_0 = FSK * Porteuse_0
    Produit_1 = FSK * Porteuse_1

    # Intégration par période pour détecter la fréquence dominante
    y0 = []
    y1 = []
    for i in range(0, len(FSK), Ns):
        y0.append(np.trapz(Produit_0[i:i + Ns]))  # Intégration pour Fp0
        y1.append(np.trapz(Produit_1[i:i + Ns]))  # Intégration pour Fp1

    # Comparaison pour extraire les bits
    bits_FSK = [1 if y1[i] > y0[i] else 0 for i in range(len(y0))]

    return bits_chiffre


# === Vérification de la modulation choisie ===


def verif_modulation():
    if Modulation == 'ASK' : 
        return(demodulation_ASK())
    else : 
        return(demodulation_FSK())



# **Décodage du signal Manchester Thomas**
bits_decodes = []
for i in range(0, len(verif_modulation()), 2):  # Lire par paires (10 → 1, 01 → 0)
    if i + 1 < len(verif_modulation()):  
        pair = (verif_modulation()[i], verif_modulation()[i+1])
        if pair == (1, 0):
            bits_decodes.append(1)  # 10 → 1
        elif pair == (0, 1):
            bits_decodes.append(0)  # 01 → 0
        else:
            print(f"Erreur de Manchester à la position {i}: {pair}")

print(bits_decodes)




# Conversion des bits en texte (ASCII 7 bits)
message_recu = ''.join(chr(int(''.join(map(str, bits_decodes[i:i+7])), 2)) 
                       for i in range(0, len(bits_decodes), 7))


print("Message reçu :", message_recu)


# Acusé de réception

t = np.linspace(0, 0.15, 5000) 
acuse_reception = np.sin(2*np.pi*5000*t)
if message_recu == message : 
    sd.play(acuse_reception)
