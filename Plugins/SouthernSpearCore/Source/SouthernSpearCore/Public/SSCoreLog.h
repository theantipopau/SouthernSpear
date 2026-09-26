// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Logging/LogMacros.h"

/**
 * The single log category for SouthernSpearCore (LogSSCore).
 *
 * Everything that fails to validate in this module reports through here rather
 * than through a bare ensure or a silent early-out, because a wrong team or
 * locality resolution is a fairness bug and must be visible in the log rather
 * than quietly defaulted.
 */
SSCORE_API DECLARE_LOG_CATEGORY_EXTERN(LogSSCore, Log, All);
