let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-25.05";
  pkgs = import nixpkgs { config = {}; overlays = []; };
in

pkgs.mkShellNoCC {
  packages = with pkgs; [
    python314
    uv
    postgresql
  ];

  shellHook = ''
    # 1. Definir función de limpieza y registrar el trap
    cleanup_postgres() {
      echo "Deteniendo PostgreSQL local…"
      pg_ctl -D "$PWD/.postgres" stop -m fast 2>/dev/null || true
    }
    trap cleanup_postgres EXIT

    # 2. Creación condicional del venv con uv
    if [ ! -d ".venv" ]; then
      echo "No se encontró .venv. Creando entorno virtual bare..."
      uv init --bare
    fi

    # 3. Activación del entorno virtual
    if [ -f ".venv/bin/activate" ]; then
      source .venv/bin/activate
    else
      # En entornos bare creados con uv, asegura que los binarios queden en PATH
      export VIRTUAL_ENV="$PWD/.venv"
      export PATH="$VIRTUAL_ENV/bin:$PATH"
    fi
  '';
}
