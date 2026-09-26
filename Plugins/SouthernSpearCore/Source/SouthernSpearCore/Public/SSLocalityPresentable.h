// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "SSTeamTypes.h"
#include "SSLocalityPresentable.generated.h"

UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class USSLocalityPresentable : public UInterface
{
	GENERATED_BODY()
};

/**
 * Something whose look depends on the local viewer's relation to it (ADR-003,
 * ADR-017). The viewer's client resolves locality and calls this; nothing
 * here is replicated and gameplay never reads it (ADR-004).
 */
class SSCORE_API ISSLocalityPresentable
{
	GENERATED_BODY()

public:
	virtual void ApplyViewerLocality(ESSLocality Locality) = 0;
};
