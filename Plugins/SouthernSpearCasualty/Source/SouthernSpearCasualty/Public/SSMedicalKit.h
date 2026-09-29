// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSCasualtyRules.h"
#include "SSMedicalKit.generated.h"

class UStaticMeshComponent;

/**
 * A medic's dropped kit (ADR-040): a treatment point, not a healing aura. Nothing happens to a soldier
 * standing beside it; they take a dressing from it or treat themselves at it, each spending a charge.
 * Server-authoritative; the charge count replicates for the HUD. Removes itself when it is empty or old.
 */
UCLASS()
class SSCASUALTY_API ASSMedicalKit : public AActor
{
	GENERATED_BODY()

public:
	ASSMedicalKit();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Server: drop a kit at Location. */
	static ASSMedicalKit* Drop(UWorld* World, const FVector& Location, AActor* Owner);

	/** The nearest usable kit within RadiusCm of Location, or null. */
	static ASSMedicalKit* FindNearest(UWorld* World, const FVector& Location, float RadiusCm);

	int32 GetCharges() const { return Charges; }
	float GetRemainingSeconds() const;
	bool IsUsable() const;

	/** Server: the state as the rules see it, and write it back after they've changed it. */
	SSCasualty::FKit ToRuleKit() const;
	void FromRuleKit(const SSCasualty::FKit& Kit);

private:
	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY(Replicated) int32 Charges = 8;
	UPROPERTY(Replicated) float Age = 0.f;
};
