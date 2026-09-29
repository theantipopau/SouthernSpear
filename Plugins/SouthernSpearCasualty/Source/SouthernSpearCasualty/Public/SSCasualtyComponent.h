// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSCasualtyRules.h"
#include "SSCasualtyComponent.generated.h"

class ASSMedicalKit;

/**
 * One soldier's casualty state (ADR-040), on the pawn. The server owns every change and replicates the
 * result; clients only read. The rules are SSCasualty:: (engine-free, checked in SSCasualtyRuleChecks.h);
 * this component holds the state, the clock, and the treatment in progress.
 *
 * Nothing in here raises health except a completed treatment (IC-11). The Lyra bridge feeds it hits and
 * input, and reacts to OnTransition; this module never touches Lyra.
 */
UCLASS(ClassGroup = (SouthernSpear), meta = (BlueprintSpawnableComponent))
class SSCASUALTY_API USSCasualtyComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USSCasualtyComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Server: the component on Actor, created if missing. */
	static USSCasualtyComponent* FindOrAdd(AActor* Actor);

	// ---- reads (anyone) ----
	SSCasualty::EState GetState() const { return static_cast<SSCasualty::EState>(State); }
	float GetHealth() const { return Health; }
	float GetBleed() const { return Bleed; }
	float GetBleedOutRemaining() const { return BleedOutRemaining; }
	int32 GetDressings() const { return Dressings; }
	bool IsMedic() const;
	/** 0..1 while this soldier is treating someone (or themselves); 0 otherwise. */
	float GetTreatmentProgress() const { return TreatmentSeconds > 0.f ? FMath::Clamp(TreatmentElapsed / TreatmentSeconds, 0.f, 1.f) : 0.f; }
	bool IsTreating() const { return TreatmentSeconds > 0.f; }
	SSCasualty::FCasualty Snapshot() const;

	// ---- server ----

	/** A hit of RawDamage, before the zone multiplier. Cancels any treatment of this soldier. */
	SSCasualty::FHitOutcome ServerApplyHit(SSCasualty::EZone Zone, float RawDamage);

	/**
	 * Begin an action on Patient (this for self-treatment). False, changing nothing, if the rules refuse it,
	 * the patient is out of range, or this soldier is busy. Runs for the action's time, then completes.
	 */
	bool ServerBeginTreatment(USSCasualtyComponent* Patient, SSCasualty::EAction Action);

	/** Stop treating (the treater moved, or was hit, or let go of the key). */
	void ServerCancelTreatment();

	/** Take a dressing from the nearest usable kit in range. */
	bool ServerTakeDressingFromKit();

	/** Server: set the soldier up fresh (spawn, or a new round). Clears wounds and refills dressings. */
	void ServerReset();

	/** Server-side transitions for the bridge: Downed, Died. */
	DECLARE_MULTICAST_DELEGATE_TwoParams(FOnTransition, USSCasualtyComponent*, SSCasualty::ETransition);
	FOnTransition OnTransition;

private:
	void Broadcast(SSCasualty::ETransition Transition);
	void FinishTreatment();
	ASSMedicalKit* NearestKit() const;

	UPROPERTY(Replicated) uint8 State = 0;          // SSCasualty::EState
	UPROPERTY(Replicated) float Health = 100.f;
	UPROPERTY(Replicated) float Bleed = 0.f;
	UPROPERTY(Replicated) float BleedOutRemaining = 0.f;
	UPROPERTY(Replicated) int32 Dressings = 2;

	// The treatment this soldier is performing, server side. Progress replicates for the HUD.
	TWeakObjectPtr<USSCasualtyComponent> TreatingPatient;
	UPROPERTY(Replicated) float TreatmentElapsed = 0.f;
	UPROPERTY(Replicated) float TreatmentSeconds = 0.f;
	SSCasualty::EAction TreatmentAction = SSCasualty::EAction::Dressing;
	SSCasualty::ETreater TreatmentTreater = SSCasualty::ETreater::Self;
	/** Who is treating this soldier (server), so a hit can cancel it. */
	TWeakObjectPtr<USSCasualtyComponent> TreatedBy;
	bool bInitialised = false;
};
