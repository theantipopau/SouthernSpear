// Copyright Southern Spear. All Rights Reserved.

#include "SSCasualtyComponent.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"
#include "SSCasualtySettings.h"
#include "SSMedicalKit.h"

USSCasualtyComponent::USSCasualtyComponent()
{
	SetIsReplicatedByDefault(true);
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void USSCasualtyComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(USSCasualtyComponent, State);
	DOREPLIFETIME(USSCasualtyComponent, Health);
	DOREPLIFETIME(USSCasualtyComponent, Bleed);
	DOREPLIFETIME(USSCasualtyComponent, BleedOutRemaining);
	DOREPLIFETIME(USSCasualtyComponent, Dressings);
	DOREPLIFETIME(USSCasualtyComponent, TreatmentElapsed);
	DOREPLIFETIME(USSCasualtyComponent, TreatmentSeconds);
}

USSCasualtyComponent* USSCasualtyComponent::FindOrAdd(AActor* Actor)
{
	if (!Actor || !Actor->HasAuthority())
	{
		return nullptr;
	}
	if (USSCasualtyComponent* Existing = Actor->FindComponentByClass<USSCasualtyComponent>())
	{
		return Existing;
	}
	USSCasualtyComponent* Component = NewObject<USSCasualtyComponent>(Actor, TEXT("SSCasualty"));
	Component->RegisterComponent();
	Component->ServerReset();
	return Component;
}

bool USSCasualtyComponent::IsMedic() const
{
	return USSCasualtySettings::Get().bEveryoneIsMedic; // roles will replace this (GDD §4.5)
}

SSCasualty::FCasualty USSCasualtyComponent::Snapshot() const
{
	SSCasualty::FCasualty C;
	C.State = GetState();
	C.Health = Health;
	C.Bleed = Bleed;
	C.BleedOutRemaining = BleedOutRemaining;
	C.Dressings = Dressings;
	return C;
}

void USSCasualtyComponent::ServerReset()
{
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		return;
	}
	ServerCancelTreatment();
	const SSCasualty::FCasualty C = SSCasualty::MakeSoldier(USSCasualtySettings::Get().ToTuning(), IsMedic());
	State = static_cast<uint8>(C.State);
	Health = C.Health;
	Bleed = C.Bleed;
	BleedOutRemaining = C.BleedOutRemaining;
	Dressings = C.Dressings;
	TreatedBy.Reset();
	bInitialised = true;
}

void USSCasualtyComponent::Broadcast(SSCasualty::ETransition Transition)
{
	if (Transition != SSCasualty::ETransition::None)
	{
		OnTransition.Broadcast(this, Transition);
	}
}

SSCasualty::FHitOutcome USSCasualtyComponent::ServerApplyHit(SSCasualty::EZone Zone, float RawDamage)
{
	SSCasualty::FHitOutcome Outcome;
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		return Outcome;
	}
	SSCasualty::FCasualty C = Snapshot();
	Outcome = SSCasualty::ApplyHit(C, USSCasualtySettings::Get().ToTuning(), Zone, RawDamage);
	if (Outcome.Applied <= 0.f && Outcome.Transition == SSCasualty::ETransition::None && C.State == GetState() && C.Health == Health)
	{
		return Outcome; // nothing happened (zero damage, or the dead)
	}
	State = static_cast<uint8>(C.State);
	Health = C.Health;
	Bleed = C.Bleed;
	BleedOutRemaining = C.BleedOutRemaining;
	// Damage interrupts treatment in both directions: being treated, and treating.
	if (USSCasualtyComponent* Treater = TreatedBy.Get())
	{
		Treater->ServerCancelTreatment();
	}
	ServerCancelTreatment();
	Broadcast(Outcome.Transition);
	return Outcome;
}

ASSMedicalKit* USSCasualtyComponent::NearestKit() const
{
	const AActor* Owner = GetOwner();
	return Owner ? ASSMedicalKit::FindNearest(GetWorld(), Owner->GetActorLocation(), USSCasualtySettings::Get().KitRadiusCm) : nullptr;
}

bool USSCasualtyComponent::ServerBeginTreatment(USSCasualtyComponent* Patient, SSCasualty::EAction Action)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !Patient || IsTreating() || GetState() != SSCasualty::EState::Up)
	{
		return false;
	}
	const USSCasualtySettings& Settings = USSCasualtySettings::Get();
	const SSCasualty::FTuning Tuning = Settings.ToTuning();
	const bool bSelf = Patient == this;
	if (!bSelf && FVector::Distance(Patient->GetOwner()->GetActorLocation(), GetOwner()->GetActorLocation()) > Settings.TreatRangeCm)
	{
		return false;
	}
	// One treater at a time per patient.
	if (Patient->TreatedBy.IsValid() && Patient->TreatedBy.Get() != this)
	{
		return false;
	}
	const SSCasualty::ETreater Treater = bSelf ? SSCasualty::ETreater::Self : (IsMedic() ? SSCasualty::ETreater::Medic : SSCasualty::ETreater::Teammate);
	// The medic's own treatment of themselves is Self (the rules never let self-treatment be better).
	ASSMedicalKit* Kit = Action == SSCasualty::EAction::KitSelfTreat ? NearestKit() : nullptr;
	SSCasualty::FKit RuleKit = Kit ? Kit->ToRuleKit() : SSCasualty::FKit();
	if (!SSCasualty::CanStart(Patient->Snapshot(), Tuning, Action, Treater, Dressings, Kit ? &RuleKit : nullptr))
	{
		return false;
	}
	TreatingPatient = Patient;
	TreatmentAction = Action;
	TreatmentTreater = Treater;
	TreatmentElapsed = 0.f;
	TreatmentSeconds = SSCasualty::ActionSeconds(Tuning, Action, Treater);
	Patient->TreatedBy = this;
	return true;
}

void USSCasualtyComponent::ServerCancelTreatment()
{
	if (USSCasualtyComponent* Patient = TreatingPatient.Get())
	{
		if (Patient->TreatedBy.Get() == this)
		{
			Patient->TreatedBy.Reset();
		}
	}
	TreatingPatient.Reset();
	TreatmentElapsed = 0.f;
	TreatmentSeconds = 0.f;
}

void USSCasualtyComponent::FinishTreatment()
{
	USSCasualtyComponent* Patient = TreatingPatient.Get();
	const SSCasualty::EAction Action = TreatmentAction;
	const SSCasualty::ETreater Treater = TreatmentTreater;
	ServerCancelTreatment();
	if (!Patient)
	{
		return;
	}
	const SSCasualty::FTuning Tuning = USSCasualtySettings::Get().ToTuning();
	SSCasualty::FCasualty PatientState = Patient->Snapshot();
	ASSMedicalKit* Kit = Action == SSCasualty::EAction::KitSelfTreat ? NearestKit() : nullptr;
	SSCasualty::FKit RuleKit = Kit ? Kit->ToRuleKit() : SSCasualty::FKit();
	int32 MyDressings = Dressings;
	if (!SSCasualty::Complete(PatientState, Tuning, Action, Treater, MyDressings, Kit ? &RuleKit : nullptr))
	{
		return; // the situation changed while the bar filled
	}
	Dressings = MyDressings;
	Patient->State = static_cast<uint8>(PatientState.State);
	Patient->Health = PatientState.Health;
	Patient->Bleed = PatientState.Bleed;
	Patient->BleedOutRemaining = PatientState.BleedOutRemaining;
	if (Kit)
	{
		Kit->FromRuleKit(RuleKit);
	}
}

bool USSCasualtyComponent::ServerTakeDressingFromKit()
{
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		return false;
	}
	ASSMedicalKit* Kit = NearestKit();
	if (!Kit)
	{
		return false;
	}
	SSCasualty::FCasualty Me = Snapshot();
	SSCasualty::FKit RuleKit = Kit->ToRuleKit();
	if (!SSCasualty::TakeDressingFromKit(Me, RuleKit, USSCasualtySettings::Get().ToTuning(), IsMedic()))
	{
		return false;
	}
	Dressings = Me.Dressings;
	Kit->FromRuleKit(RuleKit);
	return true;
}

void USSCasualtyComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		return;
	}
	if (!bInitialised)
	{
		ServerReset();
	}

	// Wounds and the bleed-out clock. This is the only place time acts on health, and it only lowers it.
	SSCasualty::FCasualty C = Snapshot();
	const SSCasualty::ETransition Transition = SSCasualty::Tick(C, USSCasualtySettings::Get().ToTuning(), DeltaTime);
	if (C.State != GetState() || C.Health != Health || C.BleedOutRemaining != BleedOutRemaining)
	{
		State = static_cast<uint8>(C.State);
		Health = C.Health;
		BleedOutRemaining = C.BleedOutRemaining;
		Bleed = C.Bleed;
	}
	if (Transition != SSCasualty::ETransition::None)
	{
		ServerCancelTreatment();
		if (USSCasualtyComponent* Treater = TreatedBy.Get())
		{
			Treater->ServerCancelTreatment();
		}
		Broadcast(Transition);
	}

	// The treatment in progress: keep the patient in range, and finish when the bar is full.
	if (IsTreating())
	{
		const USSCasualtyComponent* Patient = TreatingPatient.Get();
		const bool bInRange = Patient && Patient->GetOwner() &&
			FVector::Distance(Patient->GetOwner()->GetActorLocation(), GetOwner()->GetActorLocation()) <= USSCasualtySettings::Get().TreatRangeCm;
		if (!bInRange || GetState() != SSCasualty::EState::Up)
		{
			ServerCancelTreatment();
		}
		else
		{
			TreatmentElapsed += DeltaTime;
			if (TreatmentElapsed >= TreatmentSeconds)
			{
				FinishTreatment();
			}
		}
	}
}
