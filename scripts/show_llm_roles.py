from hr_agent.core.settings import get_models_config

def main() -> None:
    cfg = get_models_config()
    width = max(len(r) for r in cfg.roles) if cfg.roles else 10
    for role, rc in sorted(cfg.roles.items()):
        fb = f"  -> {rc.fallback_role}" if rc.fallback_role else ""
        print(
            f"{role:<{width}}  {rc.provider:<8}  {rc.model:<40} "
            f"t={rc.temperature}  timeout={rc.timeout_s}s{fb}"
        )

if __name__ == "__main__":
    main()