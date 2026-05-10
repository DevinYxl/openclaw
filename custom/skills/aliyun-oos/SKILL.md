# Aliyun OOS Operations

## Critical Guidelines

### ACS-ECS-BulkyRunCommand Usage

When calling `StartExecution` for the public template `ACS-ECS-BulkyRunCommand` (or similar OOS templates that take `targets`):

#### ✅ Correct Target Format (Official Standard)

You **MUST** strictly follow this structure. Based on official documentation examples:

```json
{
  "targets": {
    "Type": "ResourceIds",
    "RegionId": "cn-hangzhou",
    "ResourceIds": ["i-xxx", "i-yyy"]
  }
}
```

#### ❌ Common Mistakes

1.  **Do NOT use `Values`**: `{"Values": [...]}` is for other parameter types, not for direct ID lists in this context.
2.  **Do NOT omit `Type`**: The `Type` field MUST be set to `"ResourceIds"` to tell OOS how to interpret the list.
3.  **Do NOT nest incorrectly**: `ResourceIds` must be a direct property of the `targets` object, alongside `Type` and `RegionId`.

### Why This Matters

If the structure deviates (e.g., missing `Type` or using `Values`), OOS templates may fail to resolve the target list or fallback to "select all" behavior, leading to operations running on unintended instances.

### Verification

Always check the execution log's `Parameters` section. It should match the structure above exactly.
