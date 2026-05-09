#!/usr/bin/env python3
"""
Тест для проверки Terraform конфигурации
"""

import os
import subprocess
import sys
from pathlib import Path

def test_terraform_validate():
    """Проверяет валидность Terraform конфигурации"""
    infra_dir = Path(__file__).parent.parent / "infra"
    
    if not infra_dir.exists():
        print("❌ Директория infra не найдена")
        return False
    
    try:
        # Проверяем, что terraform доступен
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True,
            cwd=infra_dir
        )
        
        if result.returncode != 0:
            print("❌ Terraform не установлен или недоступен")
            return False
        
        print(f"✅ Terraform версия: {result.stdout.strip()}")

        # Без init провайдер не скачан — validate падает на свежем клоне
        result = subprocess.run(
            ["terraform", "init", "-backend=false", "-input=false"],
            capture_output=True,
            text=True,
            cwd=infra_dir,
        )
        if result.returncode != 0:
            print(f"❌ Terraform init -backend=false failed: {result.stderr or result.stdout}")
            return False
        print("✅ Terraform init (без remote backend) выполнен")

        # Проверяем валидность конфигурации
        result = subprocess.run(
            ["terraform", "validate"],
            capture_output=True,
            text=True,
            cwd=infra_dir,
        )

        if result.returncode != 0:
            print(f"❌ Terraform validate failed: {result.stderr}")
            return False
        
        print("✅ Terraform конфигурация валидна")
        return True
        
    except FileNotFoundError:
        print("❌ Terraform не найден в PATH")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке Terraform: {e}")
        return False

def test_required_files():
    """Проверяет наличие необходимых файлов"""
    required_files = [
        "infra/main.tf",
        "infra/variables.tf", 
        "infra/outputs.tf",
        "infra/providers.tf",
        "infra/cloud-init.yml",
        ".github/workflows/terraform.yml",
        "tests.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все необходимые файлы присутствуют")
    return True

def test_tests_yml():
    """Проверяет корректность tests.yml"""
    try:
        with open("tests.yml", "r") as f:
            content = f.read()
        
        # Проверяем наличие всех необходимых полей
        required_fields = ["repo_owner", "kittygram_domain", "dockerhub_username"]
        missing_fields = []
        
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ В tests.yml отсутствуют поля: {', '.join(missing_fields)}")
            return False
        
        # Проверяем, что kittygram_domain содержит порт 9000
        if ":9000" not in content:
            print("❌ В tests.yml kittygram_domain должен содержать порт 9000")
            return False
        
        print("✅ tests.yml корректно настроен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке tests.yml: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🔍 Проверка Terraform инфраструктуры...\n")
    
    tests = [
        test_required_files,
        test_terraform_validate,
        test_tests_yml
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}\n")
    
    print(f"📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️  Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main())
