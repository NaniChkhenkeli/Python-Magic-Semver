import re
from typing import List, Union


class Version:
    def __init__(self, version):
        self.original = version
        self._parse_version(version)
    
    def _parse_version(self, version: str):
        version = version.lstrip('v')
        
        if '+' in version:
            version, self.build_metadata = version.split('+', 1)
        else:
            self.build_metadata = None
        


        if '-' in version:
            main_version, prerelease = version.split('-', 1)
        else:
            main_version = version
            prerelease = None
        
        main_parts = main_version.split('.')
        self.major = int(main_parts[0]) if len(main_parts) > 0 else 0
        self.minor = int(main_parts[1]) if len(main_parts) > 1 else 0
        
        if len(main_parts) >= 3:
            patch_part = main_parts[2]
            match = re.match(r'(\d+)(.*)$', patch_part)
            if match:
                self.patch = int(match.group(1))
                suffix = match.group(2)
                if suffix:
                    prerelease = suffix if not prerelease else f"{suffix}.{prerelease}"
            else:
                self.patch = 0
        else:
            self.patch = 0
        
        self.prerelease = self._parse_prerelease(prerelease) if prerelease else []
    
    def _parse_prerelease(self, prerelease: str) -> List[Union[int, str]]:
        if not prerelease:
            return []
        
        identifiers = []
        for part in prerelease.split('.'):
            if part.isdigit():
                identifiers.append(int(part))
            else:
                identifiers.append(part)
        
        return identifiers
    
    def _compare_prerelease(self, other_prerelease: List[Union[int, str]]) -> int:
        if not self.prerelease and not other_prerelease:
            return 0
        if not self.prerelease:
            return 1 
        if not other_prerelease:
            return -1  
        min_length = min(len(self.prerelease), len(other_prerelease))
        
        for i in range(min_length):
            left, right = self.prerelease[i], other_prerelease[i]
            
            if isinstance(left, int) and isinstance(right, int):
                if left != right:
                    return -1 if left < right else 1
            elif isinstance(left, int) and isinstance(right, str):
                return -1
            elif isinstance(left, str) and isinstance(right, int):
                return 1
            else:
                if left != right:
                    return -1 if left < right else 1
        
        if len(self.prerelease) != len(other_prerelease):
            return -1 if len(self.prerelease) < len(other_prerelease) else 1
        
        return 0
    
    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        
        self_core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        
        if self_core != other_core:
            return self_core < other_core
        
        return self._compare_prerelease(other.prerelease) < 0
    
    def __le__(self, other):
        return self < other or self == other
    
    def __gt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return not (self <= other)
    
    def __ge__(self, other):
        return self > other or self == other
    
    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return self.original
    
    def __repr__(self):
        return f"Version('{self.original}')"


def main():
    to_test = [
        ("1.0.0", "2.0.0"),
        ("1.0.0", "1.42.0"),
        ("1.2.0", "1.2.42"),
        ("1.1.0-alpha", "1.2.0-alpha.1"),
        ("1.0.1b", "1.0.10-alpha.beta"),
        ("1.0.0-rc.1", "1.0.0"),
    ]
    
    for left, right in to_test:
        assert Version(left) < Version(right), f"le failed: {left} < {right}"
        assert Version(right) > Version(left), f"ge failed: {right} > {left}"
        assert Version(right) != Version(left), f"neq failed: {right} != {left}"
    
    print("testing docstring examples:")
    print(f"Version('1.1.3') < Version('2.2.3'): {Version('1.1.3') < Version('2.2.3')}")
    print(f"Version('1.3.0') > Version('0.3.0'): {Version('1.3.0') > Version('0.3.0')}")
    print(f"Version('0.3.0b') < Version('1.2.42'): {Version('0.3.0b') < Version('1.2.42')}")
    print(f"Version('1.3.42') == Version('42.3.1'): {Version('1.3.42') == Version('42.3.1')}")
    
    print("\nTesting semver precedence examples:")
    versions = [
        '1.0.0-alpha',
        '1.0.0-alpha.1', 
        '1.0.0-alpha.beta',
        '1.0.0-beta',
        '1.0.0-beta.2',
        '1.0.0-beta.11',
        '1.0.0-rc.1',
        '1.0.0'
    ]
    
    for i in range(len(versions) - 1):
        left, right = versions[i], versions[i + 1]
        result = Version(left) < Version(right)
        print(f"Version('{left}') < Version('{right}'): {result}")
        assert result, f"precedence failed: {left} should be < {right}"
    
    print("\nTesting build metadata (should be ignored in comparisons):")
    v1 = Version('1.0.0+20130313144700')
    v2 = Version('1.0.0+different.metadata')
    print(f"Version('1.0.0+20130313144700') == Version('1.0.0+different.metadata'): {v1 == v2}")
    assert v1 == v2, "Build metadata should be ignored in comparisons"
    
    print("\nAll tests passed!")


if __name__ == "__main__":
    main()