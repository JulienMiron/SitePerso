% ============================================================================
% Classe Evaluation.cls
% Classe LaTeX personnalisée pour la création d'examens universitaires.
% Basée sur la classe "exam".
% ============================================================================

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{Evaluation}

% Chargement de la classe de base "exam"
% Utiliser \LoadClass[answers]{exam} pour afficher les réponses
\LoadClass[]{exam}

% Mode Gradescope : laisser vide {} pour impression recto-verso,
% mettre un contenu (ex: {.}) pour recto seulement (importation PDF dans Gradescope)
\def\Gradescope{}

% ============================================================================
% CHARGEMENT DES PACKAGES
% ============================================================================

% --- Packages essentiels ---
\RequirePackage{iftex}             % Détection du moteur TeX utilisé
\RequirePackage{geometry}          % Gestion des marges et dimensions de la page
\RequirePackage{enumitem}          % Personnalisation des listes (enumerate, itemize)
\RequirePackage{mathtools}         % Extension d'amsmath pour les formules mathématiques
\RequirePackage[many]{tcolorbox}   % Boîtes colorées encadrées
\RequirePackage[french]{babel}     % Typographie française (espacement, titres, etc.)
\RequirePackage{xcolor}            % Gestion avancée des couleurs
\RequirePackage{etoolbox}          % Outils de programmation LaTeX (\ifdefempty, \pretocmd, etc.)
\RequirePackage{calc}              % Calculs arithmétiques dans les dimensions LaTeX
\RequirePackage{tikz}              % Dessins et graphiques vectoriels

% --- Packages pour les mathématiques ---
\usepackage{amsmath}               % Environnements mathématiques avancés
\usepackage{amssymb}               % Symboles mathématiques supplémentaires
\usepackage{xfrac}                 % Fractions diagonales avec \sfrac
\usepackage{icomma}                % Virgule intelligente en mode mathématique (pas d'espace après)

% --- Packages pour la mise en forme ---
\usepackage{comment}               % Permet de commenter de grands blocs avec \begin{comment}
\usepackage{afterpage}             % Exécute une commande après la fin de la page courante
\usepackage{ifsym}                 % Symboles divers (dés, horloges, etc.)
\usepackage{multirow}              % Cellules fusionnées verticalement dans les tableaux
\usepackage{array}                 % Amélioration des tableaux (colonnes personnalisées)

% --- Packages pour la police et l'encodage ---
\usepackage[9pt]{extsizes}         % Tailles de police supplémentaires (ici 9pt)
\usepackage{arev}                  % Police sans-serif Arev pour le texte et les maths
\usepackage[T1]{fontenc}           % Encodage de sortie T1 (accents, caractères spéciaux)

% --- Packages pour l'insertion de documents et le code ---
\usepackage{pdfpages}              % Inclusion de pages PDF externes
\usepackage{listings}              % Affichage de code source formaté

% Configuration par défaut de listings pour le langage R
\lstset{language=R, basicstyle=\ttfamily}

% ============================================================================
% CONFIGURATION DE TIKZ
% ============================================================================

% Bibliothèques TikZ : flèches, calculs, positionnement, décorations
\usetikzlibrary{arrows.meta,calc,positioning,decorations.markings}

% Styles TikZ globaux
\tikzset{
  >={Latex[length=2.2mm]},                                              % Pointe de flèche par défaut
  dot/.style  = {circle,draw,fill=white,inner sep=1.1pt,minimum size=3.8pt}, % Point plein (graphique)
  open/.style = {circle,draw,fill=white,inner sep=1.1pt,minimum size=4pt},   % Point ouvert (graphique)
  pt/.style   = {font=\small},                                          % Étiquette de point
}

% Style pour une flèche au milieu d'un segment
\tikzset{
  mid arrow/.style={
    postaction={decorate},
    decoration={markings, mark=at position 0.5 with {\arrow{Latex}}}
  }
}

% ============================================================================
% COMMANDES PERSONNALISÉES — SYMBOLES ET DESSINS
% ============================================================================

% Case à cocher carrée pour les questions à choix multiples
\checkboxchar{
  \raisebox{-0.1cm}{
    \begin{tikzpicture}
      \draw (0,0) -- (0.5,0) -- (0.5,0.5) -- (0,0.5) -- cycle;
    \end{tikzpicture}}}

% Symbole de crochet (checkmark) dessiné avec TikZ
\def\checkmark{\tikz\fill[scale=0.4](0,.35) -- (.25,0) -- (1,.7) -- (.25,.15) -- cycle;}

% Symbole ± personnalisé dessiné avec TikZ
\newcommand{\Mypm}{\mathbin{\tikz [x=1.4ex,y=1.4ex,line width=.1ex] \draw (0.0,0) -- (1.0,0) (0.5,0.08) -- (0.5,0.92) (0.0,0.5) -- (1.0,0.5);}}

% Texte en rouge : \rouge{texte}
\newcommand{\rouge}[1]{\textcolor{red}{#1}}

% Boîte rectangulaire de dimensions #1 x #2 : \boite{largeur}{hauteur}
\newcommand{\boite}[2]{
  \raisebox{-.4cm}{
    \begin{tikzpicture}
      \draw (0,0)--(#1,0) -- (#1,#2) -- (0,#2) -- cycle;
    \end{tikzpicture}
  }
}

% Ligne horizontale en mode math de longueur #1 : \myline{longueur}
\newcommand{\myline}[1]{
  \mathrel{\raisebox{-.7ex}{
    \begin{tikzpicture}
      \draw (0,0)--(#1,0);
    \end{tikzpicture}}}
}

% Carré avec libellé à droite (pour sélection de section sur la page couverture)
\newcommand{\carresection[1]}{
  \begin{tikzpicture}
    \draw (0,0) -- (0.5,0) -- (0.5,0.5) -- (0,0.5) -- cycle;
    \draw (0.5,0.25) node[align=left, right]{#1};
  \end{tikzpicture}
}

% Séparateur décoratif (courbe ondulée avec point central)
\newcommand{\separation}{
  \centering
  \begin{tikzpicture}[scale=0.33]
    \draw (0,0) .. controls (1,1) and (2,-1) .. (3,0);
    \draw[fill=black] (3.5,0) circle (0.3cm);
    \draw (4,0) .. controls (5,-1) and (5,1) .. (7,0);
  \end{tikzpicture}
}

% ============================================================================
% COMMANDES PERSONNALISÉES — GESTION DES PAGES
% ============================================================================

% Page blanche : insère une page vide.
% En mode Gradescope, ajoute une page supplémentaire (recto seulement).
\newcommand{\pageblanche}{
  \ifdefempty{\Gradescope}{\newpage}{
    \newpage
    \thispagestyle{empty}
    \null
    \newpage
  }
}

% Page blanche simple (sans numérotation)
\newcommand\blankpage{
  \null
  \thispagestyle{empty}
  \addtocounter{page}{-1}
  \newpage
}

% Indique que l'exercice continue sur la page suivante :
%   \pagesuivante{\ref{label_exercice}}
\newcommand{\pagesuivante}[1]{
  \begingroup
    \large
    \emph{\textbf{Suite de l'exercice #1 sur la feuille suivante}}
    \medskip
    \pageblanche
    \large \emph{\textbf{Suite de l'exercice #1}}
    \medskip
  \endgroup
}

% Indique la suite d'un exercice (en haut de la page suivante) :
%   \suite{\ref{label_exercice}}
\newcommand{\suite}[1]{
  \begingroup
    \large \emph{\textbf{Suite de l'exercice #1}}
  \endgroup
}

% ============================================================================
% VARIABLES DU DOCUMENT (métadonnées de l'évaluation)
% Ces commandes sont redéfinies dans le document principal (.tex)
% ============================================================================

\providecommand{\SigleNumero}{}       % Sigle et numéro du cours (ex: MAT-1000)
\providecommand{\NomCours}{}          % Nom complet du cours
\providecommand{\DateEvaluation}{}    % Date de l'évaluation
\providecommand{\HeureEvaluation}{}   % Heure de l'évaluation
\providecommand{\Session}{}           % Session (ex: Automne 2025)
\providecommand{\NomEvaluation}{}     % Nom de l'évaluation (ex: Examen final)
\providecommand{\Ponderation}{}       % Pondération de l'évaluation (en %)
\providecommand{\SectionA}{}          % Nom de l'enseignant — section A
\providecommand{\SectionB}{}          % Nom de l'enseignant — section B
\providecommand{\SectionC}{}          % Nom de l'enseignant — section C
\providecommand{\SectionD}{}          % Nom de l'enseignant — section D
\providecommand{\Matricule}{}         % Matricule de l'étudiant
\providecommand{\Coordonnateur}{}     % Nom du coordonnateur
\providecommand{\Coordonnatrice}{}    % Nom de la coordonnatrice
\providecommand{\Enseignant}{}        % Nom de l'enseignant
\providecommand{\Directives}{}        % Directives de l'évaluation
\providecommand{\NombreLignes}{}      % Nombre de lignes (pour réponses)
\providecommand{\PapierLegal}{}       % Format papier légal (si nécessaire)
\providecommand{\EnLigne}{}           % Indicateur d'évaluation en ligne
\providecommand{\Solutions}{}         % Indicateur pour l'affichage des solutions
\providecommand{\Gradescope}{}        % Indicateur pour le mode Gradescope

% ============================================================================
% MISE EN FORME DES QUESTIONS
% ============================================================================

% Ajoute un espacement vertical avant chaque question
\pretocmd{\question}{\vspace{1\baselineskip}}{}{}

% Hauteur des lignes de réponse
\setlength\linefillheight{1cm}

% Comptabilise les points automatiquement
\addpoints

% Format d'affichage des questions selon que les points sont affichés ou non
\ifdefempty{\affichepoints}{%
  % Avec affichage des points
  \qformat{\hspace{.58cm}{\sc\textbf{Exercice~\thequestion}}%
           ~{\small(\,\totalpoints~points)}~\hfill}%
  \bonusqformat{\hspace{.58cm}{\sc\textbf{Exercice~\thequestion{} BONUS}}%
                ~{\small(\,\totalbonuspoints~points)}~\hfill}%
  \bonuspointpoints{bonus point}{points}%
}{%
  % Sans affichage des points
  \qformat{\vspace{1cm}\hspace{.58cm}{\sc\textbf{Exercice}}~\hfill}%
  \bonusqformat{\hspace{.58cm}{\sc\textbf{Exercice~\thequestion{} BONUS}}~\hfill}%
}

% ============================================================================
% EN-TÊTES ET PIEDS DE PAGE
% ============================================================================

% Pas d'en-tête sur la première page
\firstpageheader{}{}{}

% Pas d'en-tête sur les pages courantes
\runningheader{}{}{}

% Pied de page : numéro de page | sigle et nom de l'évaluation
\runningfooter{\small Page \thepage~/~\numpages}
  {\small\ifdefempty{\SigleNumero}{}{\hspace{.58cm}\SigleNumero\small\ifdefempty{\NomEvaluation}{}{~--~\NomEvaluation}}}
  {}

% ============================================================================
% PAGE COUVERTURE
% ============================================================================

% Génère automatiquement la page couverture de l'évaluation
\newcommand{\couverture}{
  \newgeometry{margin=2cm}

  % --- En-tête : logo à gauche, identification de l'étudiant à droite ---
  \begin{minipage}[t]{7cm}
    \begin{flushleft}
      \hspace{-.5cm}\includegraphics[width=5cm]{logo_ul.pdf}\\
      \hspace{-.5cm}{\sf\scriptsize \textbf{Faculté des sciences et génie}}\\[-0.2cm]
      \hspace{-.5cm}{\sf\scriptsize Département de mathématiques et statistique}\\[2cm]
    \end{flushleft}
  \end{minipage}~~~
  \begin{minipage}[t]{\textwidth-5.5cm}
    % Champ pour le prénom et nom
    \begin{tikzpicture}
      \draw (0,0) -- (10,0) -- (10,1.5) -- (0,1.5) -- cycle;
      \draw (0,0) node[below right]{\scriptsize\text{Prénom et nom}};
    \end{tikzpicture}\\[0.4cm]
    % Champ pour le numéro d'identification (NI)
    \begin{tikzpicture}
      \draw (0,0) -- (9,0) -- (9,1) -- (0,1) -- cycle;
      \draw (0,0) node[below right]{\scriptsize\text{NI (9 chiffres)}};
    \end{tikzpicture}\\[0.4cm]
    % Cases à cocher pour la section de l'enseignant
    \ifdefempty{\SectionA}{}{\carresection[\SectionA]\\}
    \ifdefempty{\SectionB}{}{\carresection[\SectionB]\\}
    \ifdefempty{\SectionC}{}{\carresection[\SectionC]\\}
    \ifdefempty{\SectionD}{}{\carresection[\SectionD]}
    \ifdefempty{\SectionA}{}{\scriptsize\text{Cochez le nom de votre enseignant}}
  \end{minipage}

  \vfill

  % --- Informations centrales de l'évaluation ---
  \begin{center}
    {\huge\textbf{\ifdefempty{\NomEvaluation}{}{\NomEvaluation}\ifdefempty{\Ponderation}{}{~(\Ponderation~\%)}}}~\\
    {\Large\ifdefempty{\NomCours}{}{\NomCours}\ifdefempty{\SigleNumero}{}{~(\SigleNumero)}}~\\
    {\Large\ifdefempty{\DateEvaluation}{}{{\DateEvaluation}}}~\\
    \smallskip
    {\LARGE\ifdefempty{\HeureEvaluation}{}{{\HeureEvaluation}}}~\\
    \ifdefempty{\Enseignant}{}{Enseignant : \Enseignant}\ifdefempty{\Enseignante}{}{Enseignante : \Enseignante}~\\
    \ifdefempty{\Coordonnateur}{}{Coordonnateur : \Coordonnateur}\ifdefempty{\Coordonnatrice}{}{Coordonnatrice : \Coordonnatrice}
  \end{center}

  \vfill

  % --- Directives de l'évaluation ---
  \ifdefempty{\Directives}{}{{\noindent\textbf{Directives de l'évaluation} \Directives}}
  \medskip

  % Rétablit les marges pour le contenu de l'examen
  \newgeometry{margin=1.7cm,left=0.7cm,bottom=1.5cm,footskip = 0mm}
}

\ProcessOptions

% Génère la page couverture automatiquement au début du document
\AtBeginDocument{\couverture}

