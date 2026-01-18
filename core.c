#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <shlwapi.h>
#include <wchar.h>

#pragma comment(lib, "shlwapi.lib")

// 浏览器类型定义
typedef enum {
    BROWSER_CHROME,
    BROWSER_FIREFOX,
    BROWSER_EDGE,
    BROWSER_SAFARI,
    BROWSER_DEFAULT,
    BROWSER_UNKNOWN
} BrowserType;

// 规则结构体
typedef struct {
    int id;
    char* pattern;
    BrowserType browser;
    char* description;
} Rule;

// 配置结构体
typedef struct {
    bool auto_start;
    bool lock_position;
    bool lock_size;
    bool lock_ratio;
    int window_x;
    int window_y;
    int window_width;
    int window_height;
    int font_size;
    char* font_family;
    float opacity;
    int border_thickness;
    float scale_factor;
} Config;

// 浏览器路径缓存
typedef struct {
    BrowserType type;
    char* path;
} BrowserPathCache;

#define MAX_CACHE_ENTRIES 10
#define MAX_RULES 100
#define MAX_PATH_LENGTH 512
#define MAX_URL_LENGTH 1024
#define MAX_PATTERN_LENGTH 256

// 全局变量
BrowserPathCache browser_cache[MAX_CACHE_ENTRIES] = {0};
int cache_count = 0;

// 浏览器名称映射
const char* BROWSER_NAMES[] = {
    "chrome",
    "firefox",
    "edge",
    "safari",
    "default",
    "unknown"
};

// 浏览器可执行文件名
const char* BROWSER_EXES[] = {
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "safari.exe",
    NULL,
    NULL
};

// 注册表路径
const char* CHROME_REG_PATHS[] = {
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe",
    "SOFTWARE\\Clients\\StartMenuInternet\\Google Chrome\\shell\\open\\command",
    "SOFTWARE\\WOW6432Node\\Clients\\StartMenuInternet\\Google Chrome\\shell\\open\\command"
};

const char* FIREFOX_REG_PATHS[] = {
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\firefox.exe",
    "SOFTWARE\\Clients\\StartMenuInternet\\Firefox-308046B0AF4A39CB\\shell\\open\\command",
    "SOFTWARE\\WOW6432Node\\Clients\\StartMenuInternet\\Firefox-308046B0AF4A39CB\\shell\\open\\command"
};

const char* EDGE_REG_PATHS[] = {
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe",
    "SOFTWARE\\Clients\\StartMenuInternet\\Microsoft Edge\\shell\\open\\command",
    "SOFTWARE\\WOW6432Node\\Clients\\StartMenuInternet\\Microsoft Edge\\shell\\open\\command"
};

const char* SAFARI_REG_PATHS[] = {
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\safari.exe"
};

// 常见浏览器安装路径
const char* COMMON_BROWSER_PATHS[] = {
    "%LOCALAPPDATA%\\Microsoft\\Edge\\Application",
    "C:\\Program Files\\Google\\Chrome\\Application",
    "C:\\Program Files\\Mozilla Firefox",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application",
    "C:\\Program Files (x86)\\Mozilla Firefox",
    "%LOCALAPPDATA%\\Programs\\Microsoft Edge",
    "%LOCALAPPDATA%\\Programs\\Firefox",
    "%LOCALAPPDATA%\\Programs\\Chrome"
};

// 获取注册表值
char* get_reg_value(const char* key_path, const char* value_name, HKEY hive) {
    HKEY hKey;
    char* result = NULL;
    DWORD buffer_size = 0;
    DWORD type;

    // 打开注册表键
    if (RegOpenKeyExA(hive, key_path, 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        // 第一次调用获取所需缓冲区大小
        if (RegQueryValueExA(hKey, value_name, NULL, &type, NULL, &buffer_size) == ERROR_SUCCESS) {
            if (type == REG_SZ) {
                result = (char*)malloc(buffer_size);
                if (result) {
                    // 第二次调用获取实际值
                    if (RegQueryValueExA(hKey, value_name, NULL, &type, (LPBYTE)result, &buffer_size) != ERROR_SUCCESS) {
                        free(result);
                        result = NULL;
                    }
                }
            }
        }
        RegCloseKey(hKey);
    }

    return result;
}

// 从缓存获取浏览器路径
char* get_browser_path_from_cache(BrowserType type) {
    for (int i = 0; i < cache_count; i++) {
        if (browser_cache[i].type == type) {
            return strdup(browser_cache[i].path);
        }
    }
    return NULL;
}

// 添加浏览器路径到缓存
void add_browser_path_to_cache(BrowserType type, const char* path) {
    if (cache_count < MAX_CACHE_ENTRIES) {
        browser_cache[cache_count].type = type;
        browser_cache[cache_count].path = strdup(path);
        cache_count++;
    }
}

// 查找浏览器路径
char* find_browser_path(BrowserType type) {
    // 检查默认浏览器
    if (type == BROWSER_DEFAULT) {
        return NULL;
    }

    // 检查缓存
    char* cached_path = get_browser_path_from_cache(type);
    if (cached_path) {
        return cached_path;
    }

    const char* exe_name = BROWSER_EXES[type];
    if (!exe_name) {
        return NULL;
    }

    char* browser_path = NULL;
    const char** reg_paths = NULL;
    int reg_path_count = 0;

    // 根据浏览器类型选择注册表路径
    switch (type) {
        case BROWSER_CHROME:
            reg_paths = CHROME_REG_PATHS;
            reg_path_count = sizeof(CHROME_REG_PATHS) / sizeof(CHROME_REG_PATHS[0]);
            break;
        case BROWSER_FIREFOX:
            reg_paths = FIREFOX_REG_PATHS;
            reg_path_count = sizeof(FIREFOX_REG_PATHS) / sizeof(FIREFOX_REG_PATHS[0]);
            break;
        case BROWSER_EDGE:
            reg_paths = EDGE_REG_PATHS;
            reg_path_count = sizeof(EDGE_REG_PATHS) / sizeof(EDGE_REG_PATHS[0]);
            break;
        case BROWSER_SAFARI:
            reg_paths = SAFARI_REG_PATHS;
            reg_path_count = sizeof(SAFARI_REG_PATHS) / sizeof(SAFARI_REG_PATHS[0]);
            break;
        default:
            return NULL;
    }

    // 1. 检查系统PATH
    char path_env[MAX_PATH_LENGTH];
    if (GetEnvironmentVariableA("PATH", path_env, MAX_PATH_LENGTH)) {
        char* token = strtok(path_env, ";");
        while (token != NULL) {
            char full_path[MAX_PATH_LENGTH];
            snprintf(full_path, MAX_PATH_LENGTH, "%s\\%s", token, exe_name);
            if (PathFileExistsA(full_path)) {
                browser_path = strdup(full_path);
                goto found;
            }
            token = strtok(NULL, ";");
        }
    }

    // 2. 检查注册表
    for (int i = 0; i < reg_path_count; i++) {
        char* reg_value = get_reg_value(reg_paths[i], "", HKEY_LOCAL_MACHINE);
        if (!reg_value) {
            reg_value = get_reg_value(reg_paths[i], "", HKEY_CURRENT_USER);
        }
        
        if (reg_value) {
            char* path = NULL;
            // 处理带引号的路径
            if (reg_value[0] == '"') {
                char* end_quote = strchr(reg_value + 1, '"');
                if (end_quote) {
                    int path_len = end_quote - (reg_value + 1);
                    path = (char*)malloc(path_len + 1);
                    strncpy(path, reg_value + 1, path_len);
                    path[path_len] = '\0';
                }
            } else {
                // 提取第一个空格前的路径
                char* space = strchr(reg_value, ' ');
                if (space) {
                    int path_len = space - reg_value;
                    path = (char*)malloc(path_len + 1);
                    strncpy(path, reg_value, path_len);
                    path[path_len] = '\0';
                } else {
                    path = strdup(reg_value);
                }
            }
            
            free(reg_value);
            
            if (path && PathFileExistsA(path)) {
                browser_path = path;
                goto found;
            }
            
            if (path) {
                free(path);
            }
        }
    }

    // 3. 检查常见路径
    for (int i = 0; i < sizeof(COMMON_BROWSER_PATHS) / sizeof(COMMON_BROWSER_PATHS[0]); i++) {
        char expanded_path[MAX_PATH_LENGTH];
        if (ExpandEnvironmentStringsA(COMMON_BROWSER_PATHS[i], expanded_path, MAX_PATH_LENGTH)) {
            char full_path[MAX_PATH_LENGTH];
            snprintf(full_path, MAX_PATH_LENGTH, "%s\\%s", expanded_path, exe_name);
            if (PathFileExistsA(full_path)) {
                browser_path = strdup(full_path);
                goto found;
            }
        }
    }

found:
    if (browser_path) {
        add_browser_path_to_cache(type, browser_path);
    } else {
        // 返回可执行文件名，依赖系统PATH
        browser_path = strdup(exe_name);
    }

    return browser_path;
}

// 解析URL，提取域名
char* extract_domain(const char* url) {
    if (!url) {
        return NULL;
    }

    char* domain = NULL;
    char* url_copy = strdup(url);
    if (!url_copy) {
        return NULL;
    }

    // 移除协议前缀
    char* protocol_end = strstr(url_copy, "://");
    if (protocol_end) {
        protocol_end += 3;
    } else {
        protocol_end = url_copy;
    }

    // 提取域名（到第一个/或:为止）
    char* domain_end = strpbrk(protocol_end, "/:");
    if (domain_end) {
        int domain_len = domain_end - protocol_end;
        domain = (char*)malloc(domain_len + 1);
        strncpy(domain, protocol_end, domain_len);
        domain[domain_len] = '\0';
    } else {
        domain = strdup(protocol_end);
    }

    free(url_copy);
    return domain;
}

// 将字符串转换为浏览器类型
BrowserType string_to_browser(const char* browser_str) {
    if (!browser_str) {
        return BROWSER_UNKNOWN;
    }

    for (int i = 0; i < sizeof(BROWSER_NAMES) / sizeof(BROWSER_NAMES[0]); i++) {
        if (strcmp(browser_str, BROWSER_NAMES[i]) == 0) {
            return (BrowserType)i;
        }
    }

    return BROWSER_UNKNOWN;
}

// 匹配规则
BrowserType match_rule(const char* url, Rule* rules, int rule_count) {
    if (!url || !rules || rule_count <= 0) {
        return BROWSER_DEFAULT;
    }

    char* url_copy = strdup(url);
    if (!url_copy) {
        return BROWSER_DEFAULT;
    }

    // 替换自定义协议
    char* protocol_pos = strstr(url_copy, "urlrule://");
    if (protocol_pos) {
        memmove(protocol_pos, "http://", 7);
    }

    char* domain = extract_domain(url_copy);
    if (!domain) {
        free(url_copy);
        return BROWSER_DEFAULT;
    }

    BrowserType matched_browser = BROWSER_DEFAULT;

    // 查找匹配的规则
    for (int i = 0; i < rule_count; i++) {
        const char* pattern = rules[i].pattern;
        if (!pattern) {
            continue;
        }

        // 精确匹配域名
        if (strcmp(pattern, domain) == 0) {
            matched_browser = rules[i].browser;
            break;
        }

        // 子域名匹配（.pattern在域名中）
        char* subdomain_pos = strstr(domain, pattern);
        if (subdomain_pos && (subdomain_pos == domain || *(subdomain_pos - 1) == '.')) {
            matched_browser = rules[i].browser;
            break;
        }

        // URL包含匹配
        if (strstr(url_copy, pattern)) {
            matched_browser = rules[i].browser;
            break;
        }
    }

    free(domain);
    free(url_copy);
    return matched_browser;
}

// 启动浏览器
bool launch_browser(const char* browser_path, const char* url) {
    if (!url) {
        return false;
    }

    bool success = false;

    if (browser_path) {
        // 使用指定浏览器
        char command[MAX_PATH_LENGTH + MAX_URL_LENGTH + 2];
        snprintf(command, sizeof(command), "\"%s\" \"%s\"", browser_path, url);
        
        STARTUPINFOA si;
        PROCESS_INFORMATION pi;
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        ZeroMemory(&pi, sizeof(pi));

        success = CreateProcessA(NULL, command, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi) != 0;
        
        if (success) {
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
        }
    } else {
        // 使用默认浏览器
        success = ShellExecuteA(NULL, "open", url, NULL, NULL, SW_SHOWNORMAL) > (HINSTANCE)32;
    }

    return success;
}

// 注册URL协议
bool register_protocol(const char* protocol_name, const char* exe_path) {
    if (!protocol_name || !exe_path) {
        return false;
    }

    char key_path[MAX_PATH_LENGTH];
    char command[MAX_PATH_LENGTH + MAX_PATH_LENGTH + 10];

    // 创建协议键
    snprintf(key_path, sizeof(key_path), "Software\\Classes\\%s", protocol_name);
    HKEY hKey;
    LONG result = RegCreateKeyExA(HKEY_CURRENT_USER, key_path, 0, NULL, REG_OPTION_NON_VOLATILE,
                                  KEY_WRITE, NULL, &hKey, NULL);
    if (result != ERROR_SUCCESS) {
        return false;
    }

    // 设置协议描述
    RegSetValueExA(hKey, NULL, 0, REG_SZ, (LPBYTE)"URL:URL Browser Rule Protocol", sizeof("URL:URL Browser Rule Protocol"));
    RegSetValueExA(hKey, "URL Protocol", 0, REG_SZ, (LPBYTE)"", 1);
    RegCloseKey(hKey);

    // 设置默认图标
    snprintf(key_path, sizeof(key_path), "Software\\Classes\\%s\\DefaultIcon", protocol_name);
    result = RegCreateKeyExA(HKEY_CURRENT_USER, key_path, 0, NULL, REG_OPTION_NON_VOLATILE,
                             KEY_WRITE, NULL, &hKey, NULL);
    if (result != ERROR_SUCCESS) {
        return false;
    }

    snprintf(command, sizeof(command), "%s,0", exe_path);
    RegSetValueExA(hKey, NULL, 0, REG_SZ, (LPBYTE)command, strlen(command) + 1);
    RegCloseKey(hKey);

    // 设置命令处理
    snprintf(key_path, sizeof(key_path), "Software\\Classes\\%s\\shell\\open\\command", protocol_name);
    result = RegCreateKeyExA(HKEY_CURRENT_USER, key_path, 0, NULL, REG_OPTION_NON_VOLATILE,
                             KEY_WRITE, NULL, &hKey, NULL);
    if (result != ERROR_SUCCESS) {
        return false;
    }

    snprintf(command, sizeof(command), "\"%s\" \"%%1\"", exe_path);
    RegSetValueExA(hKey, NULL, 0, REG_SZ, (LPBYTE)command, strlen(command) + 1);
    RegCloseKey(hKey);

    return true;
}

// 简单的JSON解析（仅支持本程序所需的格式）
// 注意：这是一个简化的JSON解析器，仅用于演示，不处理所有JSON格式
bool parse_json_file(const char* file_path, void** data, int* count, bool is_config) {
    // 实际项目中应该使用成熟的JSON库，如cJSON或Jansson
    // 这里为了简化，我们只返回默认值
    if (is_config) {
        Config* config = (Config*)malloc(sizeof(Config));
        if (!config) {
            return false;
        }
        
        // 设置默认配置
        config->auto_start = false;
        config->lock_position = false;
        config->lock_size = false;
        config->lock_ratio = true;
        config->window_x = 100;
        config->window_y = 100;
        config->window_width = 500;
        config->window_height = 100;
        config->font_size = 12;
        config->font_family = strdup("Arial");
        config->opacity = 0.8f;
        config->border_thickness = 2;
        config->scale_factor = 1.0f;
        
        *data = config;
        *count = 1;
    } else {
        // 默认规则
        Rule* rules = (Rule*)malloc(3 * sizeof(Rule));
        if (!rules) {
            return false;
        }
        
        // Google使用Chrome
        rules[0].id = 1;
        rules[0].pattern = strdup("google.com");
        rules[0].browser = BROWSER_CHROME;
        rules[0].description = strdup("Google使用Chrome");
        
        // Bing使用Firefox
        rules[1].id = 2;
        rules[1].pattern = strdup("bing.com");
        rules[1].browser = BROWSER_FIREFOX;
        rules[1].description = strdup("Bing使用Firefox");
        
        // Edge官网使用Edge
        rules[2].id = 3;
        rules[2].pattern = strdup("edge.microsoft.com");
        rules[2].browser = BROWSER_EDGE;
        rules[2].description = strdup("Edge官网使用Edge");
        
        *data = rules;
        *count = 3;
    }
    
    return true;
}

// 保存JSON文件
bool save_json_file(const char* file_path, void* data, int count, bool is_config) {
    // 实际项目中应该使用成熟的JSON库
    // 这里为了简化，我们只返回true
    return true;
}

// 导出函数，供Python调用
__declspec(dllexport) char* __cdecl FindBrowserPath(const char* browser_name) {
    BrowserType type = string_to_browser(browser_name);
    return find_browser_path(type);
}

__declspec(dllexport) char* __cdecl ExtractDomain(const char* url) {
    return extract_domain(url);
}

__declspec(dllexport) const char* __cdecl MatchRule(const char* url, Rule* rules, int rule_count) {
    BrowserType browser = match_rule(url, rules, rule_count);
    return BROWSER_NAMES[browser];
}

__declspec(dllexport) bool __cdecl LaunchBrowser(const char* browser_path, const char* url) {
    return launch_browser(browser_path, url);
}

__declspec(dllexport) bool __cdecl RegisterProtocol(const char* protocol_name, const char* exe_path) {
    return register_protocol(protocol_name, exe_path);
}

__declspec(dllexport) void* __cdecl ParseJsonFile(const char* file_path, int* count, bool is_config) {
    void* data;
    if (parse_json_file(file_path, &data, count, is_config)) {
        return data;
    }
    return NULL;
}

__declspec(dllexport) bool __cdecl SaveJsonFile(const char* file_path, void* data, int count, bool is_config) {
    return save_json_file(file_path, data, count, is_config);
}

// 初始化函数
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            // 初始化缓存
            cache_count = 0;
            for (int i = 0; i < MAX_CACHE_ENTRIES; i++) {
                browser_cache[i].type = BROWSER_UNKNOWN;
                browser_cache[i].path = NULL;
            }
            break;
        case DLL_THREAD_ATTACH:
        case DLL_THREAD_DETACH:
        case DLL_PROCESS_DETACH:
            // 清理缓存
            for (int i = 0; i < cache_count; i++) {
                if (browser_cache[i].path) {
                    free(browser_cache[i].path);
                    browser_cache[i].path = NULL;
                }
            }
            cache_count = 0;
            break;
    }
    return TRUE;
}
