"""
Configuration Loader for AI Vehicle Diagnostic Agent

Loads and validates YAML configuration with environment variable substitution.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AIBackendConfig:
    """AI backend configuration"""
    primary: str
    fallbacks: list[str] = field(default_factory=list)
    claude: Dict[str, Any] = field(default_factory=dict)
    openai: Dict[str, Any] = field(default_factory=dict)
    ollama: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VehicleConfig:
    """Vehicle communication configuration"""
    port: str
    baud_rate: int = 38400
    timeout: int = 5
    protocol: str = "auto"


@dataclass
class SafetyConfig:
    """Safety configuration"""
    confirmation_level: str = "dangerous_only"
    danger_levels: Dict[str, str] = field(default_factory=dict)
    require_parking_brake: bool = True
    allow_bypass: bool = False


@dataclass
class WebResearchConfig:
    """Web research configuration"""
    mode: str = "ai_assisted"
    fallback_to_user: bool = True
    timeout: int = 30
    source_priority: list[str] = field(default_factory=list)
    cross_reference_models: bool = True


@dataclass
class KnowledgeBaseConfig:
    """Knowledge base configuration"""
    path: str = "knowledge_base/"
    auto_save: bool = True
    auto_save_threshold: float = 0.8


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    directory: str = "logs/"
    session_format: str = "jsonl"
    log_obd_traffic: bool = True
    rotate_size_mb: int = 10
    retention_days: int = 30


@dataclass
class ReportsConfig:
    """Report configuration"""
    default_format: str = "markdown"
    include_raw_data: bool = True
    include_ai_analysis: bool = True


@dataclass
class AdvancedConfig:
    """Advanced configuration"""
    enable_script_generation: bool = True
    script_timeout: int = 60
    enable_module_discovery: bool = True
    can_capture_duration: int = 10


@dataclass
class AgentConfig:
    """Complete agent configuration"""
    ai_backend: AIBackendConfig
    vehicle: VehicleConfig
    safety: SafetyConfig
    web_research: WebResearchConfig
    knowledge_base: KnowledgeBaseConfig
    logging: LoggingConfig
    reports: ReportsConfig
    advanced: AdvancedConfig


class ConfigurationError(Exception):
    """Configuration validation error"""
    pass


class ConfigLoader:
    """Load and validate agent configuration"""
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]+))?\}')
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to configuration file (default: config/agent_config.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "agent_config.yaml"
        
        self.config_path = Path(config_path)
        self._raw_config: Optional[Dict[str, Any]] = None
        self._config: Optional[AgentConfig] = None
    
    def load(self) -> AgentConfig:
        """
        Load and validate configuration
        
        Returns:
            AgentConfig object
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Load YAML file
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML syntax: {e}")
        
        if not self._raw_config:
            raise ConfigurationError("Configuration file is empty")
        
        # Substitute environment variables
        self._raw_config = self._substitute_env_vars(self._raw_config)
        
        # Validate and build configuration objects
        try:
            self._config = self._build_config(self._raw_config)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
        
        return self._config
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in configuration
        
        Format: ${VAR_NAME} or ${VAR_NAME:default_value}
        
        Args:
            obj: Configuration object (dict, list, or string)
            
        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_var_string(obj)
        else:
            return obj
    
    def _substitute_env_var_string(self, value: str) -> str:
        """
        Substitute environment variables in a string
        
        Args:
            value: String potentially containing ${VAR} or ${VAR:default}
            
        Returns:
            String with variables substituted
        """
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2)
            
            env_value = os.environ.get(var_name)
            
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # Variable not set and no default
                raise ConfigurationError(
                    f"Environment variable '{var_name}' is not set and no default provided"
                )
        
        return self.ENV_VAR_PATTERN.sub(replacer, value)
    
    def _build_config(self, raw: Dict[str, Any]) -> AgentConfig:
        """
        Build typed configuration objects from raw dictionary
        
        Args:
            raw: Raw configuration dictionary
            
        Returns:
            AgentConfig object
        """
        # Validate required sections
        required_sections = ['ai_backend', 'vehicle', 'safety', 'web_research']
        for section in required_sections:
            if section not in raw:
                raise ConfigurationError(f"Missing required section: {section}")
        
        # Build AI backend config
        ai_backend_raw = raw['ai_backend']
        ai_backend = AIBackendConfig(
            primary=ai_backend_raw.get('primary', 'claude'),
            fallbacks=ai_backend_raw.get('fallbacks', []),
            claude=ai_backend_raw.get('claude', {}),
            openai=ai_backend_raw.get('openai', {}),
            ollama=ai_backend_raw.get('ollama', {})
        )
        
        # Validate primary backend
        valid_backends = ['claude', 'openai', 'ollama']
        if ai_backend.primary not in valid_backends:
            raise ConfigurationError(
                f"Invalid primary backend: {ai_backend.primary}. "
                f"Must be one of: {', '.join(valid_backends)}"
            )
        
        # Build vehicle config
        vehicle_raw = raw['vehicle']
        vehicle = VehicleConfig(
            port=vehicle_raw.get('port', 'COM3'),
            baud_rate=vehicle_raw.get('baud_rate', 38400),
            timeout=vehicle_raw.get('timeout', 5),
            protocol=vehicle_raw.get('protocol', 'auto')
        )
        
        # Build safety config
        safety_raw = raw['safety']
        safety = SafetyConfig(
            confirmation_level=safety_raw.get('confirmation_level', 'dangerous_only'),
            danger_levels=safety_raw.get('danger_levels', {}),
            require_parking_brake=safety_raw.get('require_parking_brake', True),
            allow_bypass=safety_raw.get('allow_bypass', False)
        )
        
        # Validate confirmation level
        valid_levels = ['none', 'dangerous_only', 'all']
        if safety.confirmation_level not in valid_levels:
            raise ConfigurationError(
                f"Invalid confirmation_level: {safety.confirmation_level}. "
                f"Must be one of: {', '.join(valid_levels)}"
            )
        
        # Build web research config
        web_research_raw = raw['web_research']
        web_research = WebResearchConfig(
            mode=web_research_raw.get('mode', 'ai_assisted'),
            fallback_to_user=web_research_raw.get('fallback_to_user', True),
            timeout=web_research_raw.get('timeout', 30),
            source_priority=web_research_raw.get('source_priority', []),
            cross_reference_models=web_research_raw.get('cross_reference_models', True)
        )
        
        # Validate web research mode
        valid_modes = ['ai_assisted', 'user_fallback', 'disabled']
        if web_research.mode not in valid_modes:
            raise ConfigurationError(
                f"Invalid web_research mode: {web_research.mode}. "
                f"Must be one of: {', '.join(valid_modes)}"
            )
        
        # Build knowledge base config
        kb_raw = raw.get('knowledge_base', {})
        knowledge_base = KnowledgeBaseConfig(
            path=kb_raw.get('path', 'knowledge_base/'),
            auto_save=kb_raw.get('auto_save', True),
            auto_save_threshold=kb_raw.get('auto_save_threshold', 0.8)
        )
        
        # Build logging config
        logging_raw = raw.get('logging', {})
        logging = LoggingConfig(
            level=logging_raw.get('level', 'INFO'),
            directory=logging_raw.get('directory', 'logs/'),
            session_format=logging_raw.get('session_format', 'jsonl'),
            log_obd_traffic=logging_raw.get('log_obd_traffic', True),
            rotate_size_mb=logging_raw.get('rotate_size_mb', 10),
            retention_days=logging_raw.get('retention_days', 30)
        )
        
        # Build reports config
        reports_raw = raw.get('reports', {})
        reports = ReportsConfig(
            default_format=reports_raw.get('default_format', 'markdown'),
            include_raw_data=reports_raw.get('include_raw_data', True),
            include_ai_analysis=reports_raw.get('include_ai_analysis', True)
        )
        
        # Build advanced config
        advanced_raw = raw.get('advanced', {})
        advanced = AdvancedConfig(
            enable_script_generation=advanced_raw.get('enable_script_generation', True),
            script_timeout=advanced_raw.get('script_timeout', 60),
            enable_module_discovery=advanced_raw.get('enable_module_discovery', True),
            can_capture_duration=advanced_raw.get('can_capture_duration', 10)
        )
        
        return AgentConfig(
            ai_backend=ai_backend,
            vehicle=vehicle,
            safety=safety,
            web_research=web_research,
            knowledge_base=knowledge_base,
            logging=logging,
            reports=reports,
            advanced=advanced
        )
    
    def get_config(self) -> AgentConfig:
        """
        Get loaded configuration
        
        Returns:
            AgentConfig object
            
        Raises:
            ConfigurationError: If configuration not loaded yet
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        return self._config


def load_config(config_path: Optional[str] = None) -> AgentConfig:
    """
    Convenience function to load configuration
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        AgentConfig object
    """
    loader = ConfigLoader(config_path)
    return loader.load()


if __name__ == '__main__':
    # Test configuration loading
    try:
        config = load_config()
        print("✓ Configuration loaded successfully")
        print(f"  Primary AI backend: {config.ai_backend.primary}")
        print(f"  Vehicle port: {config.vehicle.port}")
        print(f"  Safety level: {config.safety.confirmation_level}")
        print(f"  Web research mode: {config.web_research.mode}")
    except ConfigurationError as e:
        print(f"✗ Configuration error: {e}")
